package utils

import (
	"context"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
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
