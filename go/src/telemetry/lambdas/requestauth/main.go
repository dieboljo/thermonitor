package main

import (
	"context"
	"errors"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"

	"telemetry/constants"
)

// generatePolicy is a helper function to generate an IAM policy post-authorization.
func generatePolicy(
	principalId,
	effect,
	resource string,
) events.APIGatewayCustomAuthorizerResponse {
	authResponse := events.APIGatewayCustomAuthorizerResponse{PrincipalID: principalId}

	if effect != "" && resource != "" {
		authResponse.PolicyDocument = events.APIGatewayCustomAuthorizerPolicy{
			Version: "2012-10-17",
			Statement: []events.IAMPolicyStatement{
				{
					Action:   []string{"execute-api:Invoke"},
					Effect:   effect,
					Resource: []string{resource},
				},
			},
		}
	}

	return authResponse
}

func validateToken(
	token string,
	project string,
	event *events.APIGatewayCustomAuthorizerRequestTypeRequest,
) (events.APIGatewayCustomAuthorizerResponse, error) {
	switch {
	case token == constants.SENSORS_TOKEN && project == "sensors":
		return generatePolicy("user", "Allow", event.MethodArn), nil
	case token == constants.SCITIZEN_TOKEN && project == "scitizen":
		return generatePolicy("user", "Allow", event.MethodArn), nil
	case token == constants.DOGS_TOKEN && project == "dogs":
		return generatePolicy("user", "Allow", event.MethodArn), nil
	case token == "deny":
		return generatePolicy("user", "Deny", event.MethodArn), nil
	case token == "unauthorized":
		// Return a 401 Unauthorized response
		return events.APIGatewayCustomAuthorizerResponse{}, errors.New("Unauthorized")
	default:
		return events.APIGatewayCustomAuthorizerResponse{}, errors.New("Error: Invalid token")
	}
}

// requestAuthorizer is called by AWS API Gateway to authorize requests before they
// are sent to the endpoint's associated Lambda function.
// The function associates the value provided in the
// 'authorization-token' field to the ProjectId gathered from the path.
// In this way, a single DynamoDB table can be shared between multiple projects.
func requestAuthorizer(
	ctx context.Context,
	event events.APIGatewayCustomAuthorizerRequestTypeRequest,
) (events.APIGatewayCustomAuthorizerResponse, error) {
	token := event.Headers["authorization-token"]
	project := event.PathParameters["ProjectId"]

	return validateToken(token, project, &event)
}

func main() {
	lambda.Start(requestAuthorizer)
}
