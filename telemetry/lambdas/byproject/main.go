package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go/aws"

	"telemetry/utils"
)

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Failed to load configuration, %v", err)
	}

	client := dynamodb.NewFromConfig(cfg)

	//if request.HTTPMethod == "GET" {
	//	input := &dynamodb.QueryInput{
	//		TableName: aws.String("Telemetry"),
	//		ExpressionAttributeValues: map[string]types.AttributeValue{
	//			":project": &types.AttributeValueMemberS{
	//				Value: request.PathParameters["ProjectId"],
	//			},
	//		},
	//	}

	//	start, startOk := request.QueryStringParameters["start"]
	//	end, endOk := request.QueryStringParameters["end"]

	//	switch {
	//	case startOk && endOk:
	//		input.KeyConditionExpression = aws.String(
	//			"ProjectId = :project AND EpochTime BETWEEN :start AND :end",
	//		)
	//		input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
	//			Value: start,
	//		}
	//		input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
	//			Value: end,
	//		}
	//	case startOk:
	//		input.KeyConditionExpression = aws.String(
	//			"ProjectId = :project AND EpochTime >= :start",
	//		)
	//		input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
	//			Value: start,
	//		}
	//	case endOk:
	//		input.KeyConditionExpression = aws.String(
	//			"ProjectId = :project AND EpochTime <= :end",
	//		)
	//		input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
	//			Value: end,
	//		}
	//	default:
	//		input.KeyConditionExpression = aws.String("ProjectId = :project")
	//	}

	//	output, err := utils.QueryTable(context.TODO(), client, input)
	//	if err != nil {
	//		log.Fatalf("Failed to query table, %v", err)
	//	}

	//	var items []map[string]types.AttributeValue
	//	items = append(items, output.Items...)
	//	lastEvaluatedKey := output.LastEvaluatedKey

	//	for len(lastEvaluatedKey) != 0 {
	//		input.ExclusiveStartKey = output.LastEvaluatedKey
	//		output, err = utils.QueryTable(context.TODO(), client, input)
	//		if err != nil {
	//			log.Fatalf("Failed to query table, %v", err)
	//		}
	//		lastEvaluatedKey = output.LastEvaluatedKey
	//		items = append(items, output.Items...)
	//	}

	//	json, err := json.Marshal(items)
	//	if err != nil {
	//		log.Fatalf("Could not encode results")
	//	}

	//	return events.APIGatewayProxyResponse{
	//		Body: string(json),
	//		Headers: map[string]string{
	//			"Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,authorization-token",
	//			"Access-Control-Allow-Origin":  "*",
	//			"Access-Control-Allow-Methods": "OPTIONS,POST,GET",
	//		},
	//		StatusCode: 200,
	//	}, nil
	//} else if request.HTTPMethod == "POST" {
	if request.HTTPMethod == "POST" {
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
		itemMap["ProjectId#DeviceId"] = fmt.Sprintf("%s#%s", itemMap["ProjectId"], itemMap["DeviceId"])
		fmt.Println(itemMap)
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
