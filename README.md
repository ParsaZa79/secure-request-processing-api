# Secure Request Processing API

A Flask-based API for secure request processing, featuring authentication, request queuing, and logging capabilities.

## Features

- Secure authentication system
- Secure HTTPS communication using SSL/TLS
- Request queuing and processing
- Detailed logging of requests and system events
- Database integration for storing request data
- API endpoints for submitting requests and retrieving logs

## Project Structure

```
secure-request-processing-api/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   └── __init__.py
├── instance/
├── logs/
├── migrations/
├── .env
├── config.py
├── requirements.txt
├── run.py
└── cert.pem
└── key.pem
└── README.md
```

## Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/ParsaZa79/secure-request-processing-api.git
   cd secure-request-processing-api
   ```

2. Generate self-signed SSL certificate (for development/testing purposes only):
   ```
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```

3. Set up a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

4. Configure the environment:
   - Create a `.env` file in the project root with the following variables:
     ```
     DATABASE_URL=sqlite:///yourdb.db
     GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id
     GOOGLE_OAUTH_CLIENT_SECRET=your_google_oauth_client_secret
     GOOGLE_OAUTH_REDIRECT_URI=your_google_oauth_redirect_uri
     GITHUB_OAUTH_CLIENT_ID=your_github_oauth_client_id
     GITHUB_OAUTH_CLIENT_SECRET=your_github_oauth_client_secret
     GITHUB_OAUTH_REDIRECT_URI=your_github_oauth_redirect_uri
     RABBITMQ_HOST=rabbitmq
     RABBITMQ_PORT=5672
     RABBITMQ_USER=your_rabbitmq_user
     RABBITMQ_PASS=your_rabbitmq_password
     FLASK_ENV=production
     ```
   - Adjust other configuration options in `config.py` as needed.

5. Set up the database:
   ```
   flask db upgrade
   ```

## Usage

To run the API server locally:

```
python run.py
```

The API will be available at `https://localhost:5000`.

For Docker deployment:

```
docker-compose up --build
```

This will start the API server in a Docker container, accessible at `https://localhost:443`.

Note: When using self-signed certificates, you may encounter security warnings in your browser. In a production environment, use certificates from a trusted Certificate Authority.

## Docker Deployment

1. Ensure Docker and Docker Compose are installed.

2. Build and start the containers:
   ```
   docker-compose up --build
   ```

3. The API will be available at `https://localhost:443`.

4. To stop the containers:
   ```
   docker-compose down
   ```

Note: Ensure your `.env` file is properly configured before running Docker containers.

Note: The current setup uses a self-signed SSL certificate. In a production environment, replace `cert.pem` and `key.pem` with certificates from a trusted Certificate Authority.


## SSL Configuration

This project uses SSL/TLS to secure communications. By default, it uses a self-signed certificate for HTTPS. 

- For development and testing, the provided self-signed certificate can be used.
- For production, replace `cert.pem` and `key.pem` with certificates from a trusted Certificate Authority.

To generate a new self-signed certificate:

```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Remember to never commit your SSL private key (`key.pem`) to version control.

## API Endpoints


### Request Management
- `POST /submit-request`
  - Description: Submit a new request for processing
  - Authentication: Requires OAuth authentication
  - Request Body: JSON object with `query` field (string)
  - Response: JSON object with `request_id` (integer)

- `GET /fetch-requests`
  - Description: Fetch the latest queued request
  - Authentication: Requires OAuth authentication
  - Response: JSON object with `request_id` (integer) and `query` (string), or a 404 message if queue is empty

- `POST /submit-result`
  - Description: Submit the result for a processed request
  - Authentication: Requires OAuth authentication
  - Request Body: JSON object with `request_id` (integer) and `result` (string)
  - Response: Success message or 404 if request not found

- `GET /get-result/<int:request_id>`
  - Description: Get the result of a specific request
  - Authentication: Requires OAuth authentication
  - Path Parameter: `request_id` (integer)
  - Response: JSON object with `result` (string) and `status` (string), or 404 if not found

### Log Management
- `GET /logs`
  - Description: Retrieve application logs
  - Authentication: Requires OAuth authentication
  - Response: JSON array of log entries

- `GET /logs/download`
  - Description: Download application logs as a file
  - Authentication: Requires OAuth authentication
  - Response: File download (app.log)

All endpoints are secured with OAuth authentication. Detailed request/response schemas and error responses are documented in the Swagger UI, accessible via the `/apidocs` endpoint.
For detailed API documentation, visit the `/apidocs` endpoint to access the Swagger UI.


## Load Testing

The project includes a load testing script (`benchmarking/load_test.py`) to evaluate the performance of the API under various conditions. This script allows you to simulate concurrent requests to different endpoints and measure response times and success rates.

### Features

- Concurrent request simulation using Python's `concurrent.futures`
- Support for testing multiple endpoints
- Random endpoint testing mode
- Customizable test duration and maximum concurrent requests
- Detailed performance metrics including average, max, and min response times
- Color-coded console output for easy reading of results

### Usage

1. Ensure you have installed the required dependencies:
   ```
   pip install requests colorama tqdm
   ```

2. Run the load testing script:
   ```
   python benchmarking/load_test.py
   ```

3. Follow the prompts to set the test duration and choose between sequential or random endpoint testing.

### Configuration

You can modify the following parameters in the script:

- `BASE_URL`: The base URL of your API (default: "http://localhost:8080")
- `MAX_CONCURRENT`: Maximum number of concurrent requests (default: 50)
- `ENDPOINTS`: List of endpoints to test, including method and sample data

### Output

The script provides detailed output for each tested endpoint, including:

- Number of requests completed
- Average response time
- Maximum response time
- Minimum response time
- Success rate

### Notes

- Ensure your API server is running before starting the load test.
- The script uses a placeholder session token. Replace the `get_session_token()` function with your actual authentication method.
- Adjust the `ENDPOINTS` list to match your API's available endpoints and methods.


Certainly! I've reviewed both auth.py files (in routes and utils), and I'll provide you with an updated Authentication section for your README.md. This section will reflect the current implementation of authentication in your project, including both Google and GitHub OAuth2 flows. Here's the modified Authentication section:


## Authentication

This API supports OAuth2 authentication using Google and GitHub as providers. The authentication flow is implemented to ensure secure access to the API endpoints.

### OAuth2 Authentication Flow

1. The client initiates the OAuth2 flow by redirecting to the chosen provider's (Google or GitHub) authentication page.
2. After successful authentication, the provider returns an authorization code.
3. The client sends this code to our API's auth endpoint (/api/auth/google or /api/auth/github).
4. Our API exchanges this code for access tokens with the provider.
5. The API creates or updates a user record and generates a session token.
6. The client uses this session token for subsequent API requests.

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Server
    participant P as OAuth Provider (Google/GitHub)
    participant DB as Database

    C->>A: POST /api/auth/google or /api/auth/github (with auth code)
    A->>A: Validate request
    A->>P: Exchange auth code for tokens
    P->>A: Return access token
    A->>P: Get user info using access token
    P->>A: Return user info
    A->>DB: Create/Update user record
    A->>A: Generate session token
    A->>C: Return session token

    Note over C,A: Subsequent API calls

    C->>A: Request with session token
    A->>A: Validate session token
    A->>DB: Retrieve user info
    A->>A: Process API request
    A->>C: API response

    Note over C,A: Logout

    C->>A: POST /api/auth/logout
    A->>DB: Clear session
    A->>C: Logout confirmation
```

### Using Authentication

1. Obtain a session token by completing the OAuth2 flow with either Google or GitHub.
2. Include this session token in the Authorization header for all subsequent requests:

```
Authorization: Bearer <your_session_token>
```

### Endpoints

- `POST /api/auth/google`: Authenticate using Google OAuth2
- `POST /api/auth/github`: Authenticate using GitHub OAuth2
- `POST /api/auth/logout`: Logout and invalidate the current session

### Security Measures

- Session tokens are JWT (JSON Web Tokens) encoded with user information and an expiration time.
- The `oauth_required` decorator in `utils/auth.py` validates the session token for protected routes.
- If a token is invalid or expired, the request is denied with a 401 Unauthorized response.

### Configuration

Ensure the following environment variables are set for OAuth2 to function correctly:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`
- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_CLIENT_SECRET`
- `GITHUB_OAUTH_REDIRECT_URI`
- `JWT_SECRET_KEY`

### Notes

- The current implementation uses a custom session token instead of directly using the OAuth provider's tokens. This allows for unified authentication handling across different providers.
- User information is stored in the database, allowing for user management and personalized experiences.
- Always use HTTPS in production to secure token transmission.


## Project Architecture

```mermaid
graph TD
    A[Client] -->|HTTP Request| B(Flask App)
    B --> C{Authentication}
    C -->|Success| D[Request Processing]
    C -->|Failure| E[Error Response]
    D --> F[Queue Service]
    F --> G[Database]
    D --> H[Logging Service]
    H --> I[Log Files]
```

## Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Queue
    participant DB
    participant Logger

    Client->>API: Submit Request
    API->>Auth: Authenticate
    Auth-->>API: Token
    API->>Queue: Enqueue Request
    Queue->>DB: Store Request
    API-->>Client: Request Accepted
    Queue->>API: Process Request
    API->>DB: Update Request Status
    API->>Logger: Log Request Details
```

## Deep Learning Server Simulation

The project includes a deep learning server simulation script (`script.py`) located in `deep-learning-simulation` folder to showcase how a separate server might interact with the API for processing requests. This script simulates the behavior of a deep learning server that authenticates with the API, fetches requests, processes them, and submits results back to the API.

### Features

- OAuth2 authentication with Google or GitHub
- Automatic token refresh when expired
- Continuous polling for new requests
- Simulated deep learning processing
- Submission of processed results back to the API

### Usage

1. Ensure you have installed the required dependencies:
   ```
   pip install requests python-dotenv pyjwt
   ```

2. Set up your environment variables in a `.env` file:
   ```
   GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
   GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
   GOOGLE_OAUTH_REDIRECT_URI=your_google_redirect_uri
   GITHUB_OAUTH_CLIENT_ID=your_github_client_id
   GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
   GITHUB_OAUTH_REDIRECT_URI=your_github_redirect_uri
   AUTH_CODE=your_manually_obtained_auth_code
   ```

3. Run the deep learning server simulation:
   ```
   python deep_learning_server.py
   ```

### Configuration

- `API_BASE_URL`: The base URL of your API (default: "http://localhost:5000")
- `OAUTH_PROVIDER`: The OAuth provider to use ("google" or "github")

### Workflow

1. The script authenticates with the API using the provided OAuth credentials.
2. It enters a continuous loop to:
   a. Check if the authentication token needs refreshing
   b. Fetch a new request from the API
   c. Simulate processing the request (placeholder for actual deep learning tasks)
   d. Submit the processed result back to the API
3. If no requests are available, it waits for a short period before checking again.

### Note

This script is a simulation and prototype. In a production environment, you would need to:
- Implement a proper OAuth2 flow to obtain the authorization code automatically
- Replace the simulated deep learning process with actual model inference code
- Add more robust error handling and logging
- Consider using a more sophisticated job queue system for managing requests

The script serves as a starting point to demonstrate the interaction between a deep learning server and the API in a secure, authenticated manner.


## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.