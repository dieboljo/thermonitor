package main

import (
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"

	"telemetry/utils"
)

// deviceEndpointHandler is an AWS Lambda function
// that parses the URL used to access the API Gateway.
// It uses path parameters and optional query string parameters to retrieve data
// from DynamoDB for a particular project and device.
func deviceEndpointHandler(
	request events.APIGatewayProxyRequest,
) (events.APIGatewayProxyResponse, error) {
	client := utils.InitClient()

	// This handler only handles GET requests.
	if request.HTTPMethod == "GET" {
		// The primary key is a composite key of the ProjectId and DeviceId
		primaryValue := utils.CreateCompositeKey(&request, "ProjectId", "DeviceId")

		input := utils.CreateQueryInput("ProjectId#DeviceId", primaryValue)

		// If the 'single' query string parameter exists and is truthy, fetch a single value only.
		// This value is the most recent device data or the most recent in the chosen time frame,
		// if supplied with the 'start' and/or 'end' query parameters.
		single := utils.EvaluateSingleParam(&request, input)

		// The 'start' and 'end' query string parameters
		// set the inclusive time range for queried data.
		// Both are optional, and one can be supplied without the other.
		utils.EvaluateStartEndParams(&request, input)

		items := utils.GetData(client, input, single)

		return utils.GetSuccessResponse(items)
	}
	return utils.MethodNotAllowedResponse()
}

func main() {
	lambda.Start(deviceEndpointHandler)
}
