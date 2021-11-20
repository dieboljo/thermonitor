package main

import (
	"context"
	"encoding/json"
	"log"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/aws/aws-sdk-go/aws"

	"telemetry/utils"
)

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Failed to load configuration, %v", err)
	}

	client := dynamodb.NewFromConfig(cfg)

	if request.HTTPMethod == "GET" {
		input := &dynamodb.QueryInput{
			TableName:        aws.String("TelemetryData"),
			FilterExpression: aws.String("LocationId = :location"),
			ExpressionAttributeValues: map[string]types.AttributeValue{
				":project": &types.AttributeValueMemberS{
					Value: request.PathParameters["ProjectId"],
				},
				":location": &types.AttributeValueMemberS{
					Value: request.PathParameters["LocationId"],
				},
			},
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
		lastEvaluatedKey := output.LastEvaluatedKey

		for len(lastEvaluatedKey) != 0 {
			input.ExclusiveStartKey = output.LastEvaluatedKey
			output, err = utils.QueryTable(context.TODO(), client, input)
			if err != nil {
				log.Fatalf("Failed to query table, %v", err)
			}
			lastEvaluatedKey = output.LastEvaluatedKey
			items = append(items, output.Items...)
		}

		json, err := json.Marshal(items)
		if err != nil {
			log.Fatalf("Could not encode results")
		}

		return events.APIGatewayProxyResponse{
			Body: string(json),
			Headers: map[string]string{
				"Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,authorization-token",
				"Access-Control-Allow-Origin":  "*",
				"Access-Control-Allow-Methods": "OPTIONS,POST,GET",
			},
			StatusCode: 200,
		}, nil
	}
	return events.APIGatewayProxyResponse{
		Body: "Method not supported",
		Headers: map[string]string{
			"Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,authorization-token",
			"Access-Control-Allow-Origin":  "*",
			"Access-Control-Allow-Methods": "OPTIONS,POST,GET",
		},
		StatusCode: 405,
	}, nil
}

func main() {
	lambda.Start(handler)
}
