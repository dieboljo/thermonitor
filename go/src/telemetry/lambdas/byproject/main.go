package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/aws/aws-sdk-go/aws"

	"telemetry/constants"
	"telemetry/utils"
)

func decodePostData(request *events.APIGatewayProxyRequest) map[string]interface{} {
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
	return itemMap
}

func augmentPostData(itemMap map[string]interface{}, request *events.APIGatewayProxyRequest) {
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
}

func createTableInput(item map[string]types.AttributeValue) *dynamodb.PutItemInput {
	input := &dynamodb.PutItemInput{
		TableName: aws.String(constants.TABLE_NAME),
		Item:      item,
	}
	return input
}

func tryPutItem(client *dynamodb.Client, input *dynamodb.PutItemInput) {
	_, err := utils.PutTableItem(context.TODO(), client, input)
	if err != nil {
		log.Fatalf("Failed to add to table, %v", err)
	}
}

func handleGet(
	request *events.APIGatewayProxyRequest,
	client *dynamodb.Client,
) (events.APIGatewayProxyResponse, error) {
	// For GET requests, the handler fetches project data from
	// AWS DynamoDB according to a single path parameter and optional query string parameters.
	primaryValue := request.PathParameters["ProjectId"]

	input := utils.CreateQueryInput("ProjectId", primaryValue)
	input.IndexName = aws.String("ProjectId-EpochTime-index")

	// If the 'single' query string parameter exists and is truthy, fetch a single value only.
	// This value is the most recent project data or the most recent in the chosen time frame,
	// if supplied with the 'start' and/or 'end' query parameters.
	single := utils.EvaluateSingleParam(request, input)

	utils.EvaluateStartEndParams(request, input)

	items := utils.GetData(client, input, single)

	return utils.GetSuccessResponse(items)
}

func handlePost(
	request *events.APIGatewayProxyRequest,
	client *dynamodb.Client,
) (events.APIGatewayProxyResponse, error) {
	// For POST requests, the handler puts new data into the same DynamoDB table according to the
	// same path parameter and the fields included in the POST body. In addition to the ProjectId
	// gathered from the path, the EpochTime and DeviceId fields are also required in the POST body.
	itemMap := decodePostData(request)

	augmentPostData(itemMap, request)

	item := utils.MapToAttributeValues(itemMap)

	input := createTableInput(item)

	tryPutItem(client, input)

	return utils.PostSuccessResponse()
}

// projectEndpointHandler is an AWS Lambda function that is called by AWS API Gateway.
func projectEndpointHandler(
	request events.APIGatewayProxyRequest,
) (events.APIGatewayProxyResponse, error) {

	client := utils.InitClient()
	if request.HTTPMethod == "GET" {
		return handleGet(&request, client)
	} else if request.HTTPMethod == "POST" {
		return handlePost(&request, client)
	}
	return utils.MethodNotAllowedResponse()
}

func main() {
	lambda.Start(projectEndpointHandler)
}
