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

// projectEndpointHandler is an AWS Lambda function that is called by AWS API Gateway.
// For GET requests, the handler fetches project data from
// AWS DynamoDB according to a single path parameter and optional query string parameters.
// For POST requests, the handler puts new data into the same DynamoDB table according to the
// same path parameter and the fields included in the POST body. In addition to the ProjectId
// gathered from the path, the EpochTime and DeviceId fields are also required in the POST body.
func projectEndpointHandler(
	request events.APIGatewayProxyRequest,
) (events.APIGatewayProxyResponse, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Failed to load configuration, %v", err)
	}

	client := dynamodb.NewFromConfig(cfg)

	if request.HTTPMethod == "GET" {
		input := &dynamodb.QueryInput{
			TableName: aws.String("Telemetry"),
			IndexName: aws.String("ProjectId-EpochTime-index"),
			ExpressionAttributeValues: map[string]types.AttributeValue{
				":project": &types.AttributeValueMemberS{
					Value: request.PathParameters["ProjectId"],
				},
			},
		}

		// If the 'single' query string parameter exists and is truthy, fetch a single value only.
		// This value is the most recent project data or the most recent in the chosen time frame,
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

		start, startOk := request.QueryStringParameters["start"]
		end, endOk := request.QueryStringParameters["end"]

		switch {
		case startOk && endOk:
			input.KeyConditionExpression = aws.String(
				"ProjectId = :project AND EpochTime BETWEEN :start AND :end",
			)
			input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
				Value: start,
			}
			input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
				Value: end,
			}
		case startOk:
			input.KeyConditionExpression = aws.String(
				"ProjectId = :project AND EpochTime >= :start",
			)
			input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
				Value: start,
			}
		case endOk:
			input.KeyConditionExpression = aws.String(
				"ProjectId = :project AND EpochTime <= :end",
			)
			input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
				Value: end,
			}
		default:
			input.KeyConditionExpression = aws.String("ProjectId = :project")
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
	} else if request.HTTPMethod == "POST" {
		itemBytes := []byte(request.Body)
		var itemMap map[string]interface{}

		if err := json.Unmarshal(itemBytes, &itemMap); err != nil {
			log.Fatalln("Could not decode data")
		}
		if _, epochTimeOk := itemMap["EpochTime"]; !epochTimeOk {
			log.Fatalln("EpochTime is required")
		}
		if _, deviceIDOk := itemMap["DeviceId"]; !deviceIDOk {
			log.Fatalln("DeviceId is required")
		}

		itemMap["ProjectId"] = request.PathParameters["ProjectId"]
		itemMap["ProjectId#DeviceId"] = fmt.Sprintf("%s#%s",
			itemMap["ProjectId"],
			itemMap["DeviceId"],
		)

		if locationID, locationIDOk := itemMap["LocationId"]; locationIDOk {
			itemMap["ProjectId#LocationId"] = fmt.Sprintf("%s#%s",
				itemMap["ProjectId"],
				locationID,
			)
		}

		item := utils.MapToAttributeValues(itemMap)

		input := &dynamodb.PutItemInput{
			TableName: aws.String("Telemetry"),
			Item:      item,
		}

		_, err := utils.PutTableItem(context.TODO(), client, input)
		if err != nil {
			log.Fatalf("Failed to add to table, %v", err)
		}

		return events.APIGatewayProxyResponse{
			Body: "Success! Item added",
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
	lambda.Start(projectEndpointHandler)
}
