package utils

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"telemetry/constants"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/aws/aws-sdk-go/aws"
)

// DynamoDbPutItemAPI defines interface for PutItem function.
type DynamoDbPutItemAPI interface {
	PutItem(
		ctx context.Context,
		params *dynamodb.PutItemInput,
		optFns ...func(*dynamodb.Options),
	) (*dynamodb.PutItemOutput, error)
}

// DynamoDbQueryAPI defines interface for Query function.
type DynamoDbQueryAPI interface {
	Query(
		ctx context.Context,
		params *dynamodb.QueryInput,
		optFns ...func(*dynamodb.Options),
	) (*dynamodb.QueryOutput, error)
}

// ListToAttributeValues converts a list into a list of DynamoDB AttributeValues
func ListToAttributeValues(anyList []interface{}) []types.AttributeValue {
	var attList []types.AttributeValue
	for _, value := range anyList {
		switch value.(type) {
		case string:
			attList = append(attList, &types.AttributeValueMemberS{Value: value.(string)})
		case float64:
			attList = append(attList, &types.AttributeValueMemberN{Value: fmt.Sprintf("%f", value)})
		case bool:
			attList = append(attList, &types.AttributeValueMemberBOOL{Value: value.(bool)})
		case []interface{}:
			childList := ListToAttributeValues(value.([]interface{}))
			attList = append(attList, &types.AttributeValueMemberL{Value: childList})
		case map[string]interface{}:
			childMap := MapToAttributeValues(value.(map[string]interface{}))
			attList = append(attList, &types.AttributeValueMemberM{Value: childMap})
		default:
			attList = append(attList, &types.AttributeValueMemberNULL{Value: true})
		}
	}
	return attList
}

// MapToAttributeValues converts a map into a map of DynamoDB AttributeValues
func MapToAttributeValues(anyMap map[string]interface{}) map[string]types.AttributeValue {
	attMap := make(map[string]types.AttributeValue)
	for key, value := range anyMap {
		switch value.(type) {
		case string:
			attMap[key] = &types.AttributeValueMemberS{Value: value.(string)}
		case float64:
			attMap[key] = &types.AttributeValueMemberN{Value: fmt.Sprintf("%f", value)}
		case bool:
			attMap[key] = &types.AttributeValueMemberBOOL{Value: value.(bool)}
		case []interface{}:
			childList := ListToAttributeValues(value.([]interface{}))
			attMap[key] = &types.AttributeValueMemberL{Value: childList}
		case map[string]interface{}:
			childMap := MapToAttributeValues(value.(map[string]interface{}))
			attMap[key] = &types.AttributeValueMemberM{Value: childMap}
		default:
			attMap[key] = &types.AttributeValueMemberNULL{Value: true}
		}
	}
	return attMap
}

// PutTableItem enters a single item into a DynamoDB table.
func PutTableItem(
	c context.Context,
	api DynamoDbPutItemAPI,
	input *dynamodb.PutItemInput,
) (*dynamodb.PutItemOutput, error) {
	return api.PutItem(c, input)
}

// QueryTable retrieves items by partition key and sort key.
func QueryTable(
	c context.Context,
	api DynamoDbQueryAPI,
	input *dynamodb.QueryInput,
) (*dynamodb.QueryOutput, error) {
	return api.Query(c, input)
}

func CreateCompositeKey(
	request *events.APIGatewayProxyRequest,
	param1 string,
	param2 string,
) string {
	key := fmt.Sprintf(
		"%s#%s",
		request.PathParameters[param1],
		request.PathParameters[param2],
	)
	return key
}

func CreateQueryInput(
	primaryName string,
	primaryValue string,
) *dynamodb.QueryInput {
	input := &dynamodb.QueryInput{
		TableName: aws.String(constants.TABLE_NAME),
		ExpressionAttributeNames: map[string]string{
			"#primaryName": primaryName,
		},
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":primaryValue": &types.AttributeValueMemberS{
				Value: primaryValue,
			},
		},
	}
	return input
}

func EvaluateSingleParam(
	request *events.APIGatewayProxyRequest,
	input *dynamodb.QueryInput,
) bool {
	singleStr, singleOk := request.QueryStringParameters["single"]
	single := false
	if singleOk {
		single, _ = strconv.ParseBool(singleStr)
		if single {
			input.Limit = aws.Int32(1)
			input.ScanIndexForward = aws.Bool(false)
		}
	}
	return single
}

func EvaluateStartEndParams(
	request *events.APIGatewayProxyRequest,
	input *dynamodb.QueryInput,
) {
	start, startOk := request.QueryStringParameters["start"]
	end, endOk := request.QueryStringParameters["end"]
	switch {
	case startOk && endOk:
		setTimeRange(input, start, end)
	case startOk:
		setLowerTimeBound(input, start)
	case endOk:
		setUpperTimeBound(input, end)
	default:
		input.KeyConditionExpression = aws.String("#primaryName = :primaryValue")
	}
}

func setTimeRange(input *dynamodb.QueryInput, start string, end string) {
	input.KeyConditionExpression = aws.String(
		"#primaryName = :primaryValue AND EpochTime BETWEEN :start AND :end",
	)
	input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
		Value: start,
	}
	input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
		Value: end,
	}
}

func setLowerTimeBound(input *dynamodb.QueryInput, start string) {
	input.KeyConditionExpression = aws.String(
		"#primaryName = :primaryValue AND EpochTime >= :start",
	)
	input.ExpressionAttributeValues[":start"] = &types.AttributeValueMemberN{
		Value: start,
	}
}

func setUpperTimeBound(input *dynamodb.QueryInput, end string) {
	input.KeyConditionExpression = aws.String(
		"#primaryName = :primaryValue AND EpochTime <= :end",
	)
	input.ExpressionAttributeValues[":end"] = &types.AttributeValueMemberN{
		Value: end,
	}
}

func InitClient() *dynamodb.Client {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("Failed to load configuration, %v", err)
	}

	return dynamodb.NewFromConfig(cfg)
}

func GetData(
	client *dynamodb.Client,
	input *dynamodb.QueryInput,
	single bool,
) []map[string]types.AttributeValue {
	var items []map[string]types.AttributeValue
	output, err := QueryTable(context.TODO(), client, input)
	if err != nil {
		log.Fatalf("Failed to query table, %v", err)
	}
	items = append(items, output.Items...)

	// DynamoDB paginates the results returned. If the queried data spans multiple
	// pages, the handler will send multiple requests.
	if !single {
		items = getMoreData(client, input, output.LastEvaluatedKey, items)
	}
	return items
}

func getMoreData(
	client *dynamodb.Client,
	input *dynamodb.QueryInput,
	lastKey map[string]types.AttributeValue,
	items []map[string]types.AttributeValue,
) []map[string]types.AttributeValue {
	var output *dynamodb.QueryOutput
	var err error
	for lastKey != nil {
		input.ExclusiveStartKey = lastKey
		output, err = QueryTable(context.TODO(), client, input)
		if err != nil {
			log.Fatalf("Failed to query table, %v", err)
		}
		lastKey = output.LastEvaluatedKey
		items = append(items, output.Items...)
	}
	return items
}

func GetSuccessResponse(items []map[string]types.AttributeValue) (events.APIGatewayProxyResponse, error) {
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

func PostSuccessResponse() (events.APIGatewayProxyResponse, error) {
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

func MethodNotAllowedResponse() (events.APIGatewayProxyResponse, error) {
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
