package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strconv"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/aws/aws-sdk-go/aws"

	"telemetry/utils"
)

// locationEndpointHandler is an AWS Lambda function that
// parses the URL used to access the API Gateway.
// It uses path parameters and optional query string parameters to retrieve data
// from DynamoDB for a particular project and location.
func locationEndpointHandler(
	request events.APIGatewayProxyRequest,
) (events.APIGatewayProxyResponse, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Failed to load configuration, %v", err)
	}

	client := dynamodb.NewFromConfig(cfg)

	// The handler only handles GET requests.
	if request.HTTPMethod == "GET" {
		// The primary key is a composite key of the ProjectId and LocationId
		primaryKey := fmt.Sprintf(
			"%s#%s",
			request.PathParameters["ProjectId"],
			request.PathParameters["LocationId"],
		)
		input := &dynamodb.QueryInput{
			TableName: aws.String("Telemetry"),
			IndexName: aws.String("ProjectIdLocationId-EpochTime-index"),
			ExpressionAttributeNames: map[string]string{
				"#primaryKey": "ProjectId#LocationId",
			},
			ExpressionAttributeValues: map[string]types.AttributeValue{
				":project_location": &types.AttributeValueMemberS{
					Value: primaryKey,
				},
			},
		}

		// If the 'single' query string parameter exists and is truthy, fetch a single value only.
		// This value is the most recent or the most recent in the chosen time frame,
		// if supplied with the 'start' and/or 'end' query parameters.
		singleStr, singleOk := request.QueryStringParameters["single"]
		single := false
		if singleOk {
			single, _ = strconv.ParseBool(singleStr)
			if single {
				input.Limit = aws.Int32(1)
				input.ScanIndexForward = aws.Bool(false)
			}
		}

		// The 'start' and 'end' query string parameters
		// set the inclusive time range for queried data.
		// Both are optional, and one can be supplied without the other.
		start, startOk := request.QueryStringParameters["start"]
		end, endOk := request.QueryStringParameters["end"]

		switch {
		case startOk && endOk:
			input.KeyConditionExpression = aws.String(
				"#primaryKey = :project_location AND EpochTime BETWEEN :start AND :end",
			)
			input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
				Value: start,
			}
			input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
				Value: end,
			}
		case startOk:
			input.KeyConditionExpression = aws.String(
				"#primaryKey = :project_location AND EpochTime >= :start",
			)
			input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
				Value: start,
			}
		case endOk:
			input.KeyConditionExpression = aws.String(
				"#primaryKey = :project_location AND EpochTime <= :end",
			)
			input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
				Value: end,
			}
		default:
			input.KeyConditionExpression = aws.String("#primaryKey = :project_location")
		}

		output, err := utils.QueryTable(context.TODO(), client, input)
		if err != nil {
			log.Fatalf("Failed to query table, %v", err)
		}

		var items []map[string]types.AttributeValue
		items = append(items, output.Items...)

		// DynamoDB paginates the results returned. If the queried data spans multiple
		// pages, the handler will send multiple requests.
		lastEvaluatedKey := output.LastEvaluatedKey
		if !single {
			for len(lastEvaluatedKey) != 0 {
				input.ExclusiveStartKey = output.LastEvaluatedKey
				output, err = utils.QueryTable(context.TODO(), client, input)
				if err != nil {
					log.Fatalf("Failed to query table, %v", err)
				}
				lastEvaluatedKey = output.LastEvaluatedKey
				items = append(items, output.Items...)
			}
		}

		json, err := json.Marshal(items)
		if err != nil {
			log.Fatalf("Could not encode results")
		}

		return events.APIGatewayProxyResponse{
			Body: string(json),
			// The lambda handler includes necessary CORS headers in the API Gateway response
			Headers: map[string]string{
				"Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization," +
					"X-Api-Key,X-Amz-Security-Token,authorization-token",
				"Access-Control-Allow-Origin":  "*",
				"Access-Control-Allow-Methods": "OPTIONS,POST,GET",
			},
			StatusCode: 200,
		}, nil
	}
	return events.APIGatewayProxyResponse{
		Body: "Method not supported",
		Headers: map[string]string{
			"Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization," +
				"X-Api-Key,X-Amz-Security-Token,authorization-token",
			"Access-Control-Allow-Origin":  "*",
			"Access-Control-Allow-Methods": "OPTIONS,POST,GET",
		},
		StatusCode: 405,
	}, nil
}

func main() {
	lambda.Start(locationEndpointHandler)
}
