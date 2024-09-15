
# AuthService

FastAPI Auth Service for Multi Tenant SaaS - Backend Engineer

## Setup and Run

```sh
pip install -r requirements.txt
alembic init alembic
```
Set Postgres DB Connection URL in alembic.ini (change username & password)
```python
sqlalchemy.url = postgresql://username:password@localhost/AuthService
```
Set Model Metadata in alembic/env.py
```python
from models import Base
target_metadata = Base.metadata
```
Set following environment variables in .env
```python
POSTGRES_URL=postgresql+psycopg2://username:password@localhost/AuthService
RESEND_API_KEY=re_originlapikeyhere
```
```sh
alembic upgrade head
alembic revision --autogenerate -m "Create Test, User, Organisation, Member, and Role tables"
alembic upgrade head
uvicorn main:app
```

# API Docs

## GET Hello World

`http://127.0.0.1:8000/`

Hello World!


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/'
    ```

- #### Response
    Body:
    ```json
    {
        "Hello": "World"
    }
    ```

## POST Sign-Up 

`http://127.0.0.1:8000/signup`

POST Endpoint creates an organisation and assign the user as its owner
SSO for multi organisation
Verification link sent to confirm user's email
Verification link expiry - 7 days

- ### Body
    urlencoded:
    - email: s.vickie14@gmail.com
    - password: password123  
    - org: example


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/signup' 
    --data-urlencode 'email=s.vickie14@gmail.com' 
    --data-urlencode 'password=password123' 
    --data-urlencode 'org=example'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "Verification link sent, Please verify the email"
    }
    ```
    ![verification mail](assets/verification.png)

## GET Verify-Email

`http://127.0.0.1:8000/verify-email?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiZXhwIjoxNzI2OTI4Mjg3fQ.zDj5Sa-COzuCS4lGz2WvltoEkSxTWPPliLLxIa2KNMQ`

GET Endpoint validates the user's email as legitimate

- ### Query Params

    token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiZXhwIjoxNzI2OTI4Mjg3fQ.zDj5Sa-COzuCS4lGz2WvltoEkSxTWPPliLLxIa2KNMQ


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/verify-email?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiZXhwIjoxNzI2OTI4Mjg3fQ.zDj5Sa-COzuCS4lGz2WvltoEkSxTWPPliLLxIa2KNMQ'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "User verified successfully"
    }
    ```

## POST Sign-In

`http://127.0.0.1:8000/signin`

POST Endpoint which provides JWT access and refresh tokens
access expiry -> 30mins
refresh expiry -> 7 days

- ### Body
    urlencoded:
    - email: s.vickie14@gmail.com
    - password: password123
    - org: example


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/signin' 
    --data-urlencode 'email=s.vickie14@gmail.com' 
    --data-urlencode 'password=password123' 
    --data-urlencode 'org=example'
    ```

- #### Response
    Body:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InMudmlja2llMTRAZ21haWwuY29tIiwiaWQiOjEsIm9yZyI6ImV4YW1wbGUiLCJyb2xlIjoib3duZXIiLCJleHAiOjE3MjYzMjUzNTR9.nKLPoSHETTMn9PKpATESOlIAdUtlRYdVWeYCWD7PeOA",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InMudmlja2llMTRAZ21haWwuY29tIiwiaWQiOjEsIm9yZyI6ImV4YW1wbGUiLCJyb2xlIjoib3duZXIiLCJleHAiOjE3MjY5MjgzNTR9.jLd5R8sZI37JyTu_S6hxlU3BECz-mv5yxpGalQybR_Y",
        "token_type": "bearer"
    }
    ```
    ![login mail](assets/login.png)

## POST Refresh-Token

`http://127.0.0.1:8000/refresh-token`

POST Endpoint to refresh the access token if expired while refresh token is alive.

- ### Authorization
    Bearer Token

- ### Body
    urlencoded:
    - refresh_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InMudmlja2llMTRAZ21haWwuY29tIiwiaWQiOjEsIm9yZyI6ImV4YW1wbGUiLCJyb2xlIjoib3duZXIiLCJleHAiOjE3MjY5MjgzNTR9.jLd5R8sZI37JyTu_S6hxlU3BECz-mv5yxpGalQybR_Y


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/refresh-token' 
    --data-urlencode 'refresh_token='
    ```

- #### Response
    Body:
        ```json
        {
            "message": "Access token is still valid",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InMudmlja2llMTRAZ21haWwuY29tIiwiaWQiOjEsIm9yZyI6ImV4YW1wbGUiLCJyb2xlIjoib3duZXIiLCJleHAiOjE3MjYzMjUzNTR9.nKLPoSHETTMn9PKpATESOlIAdUtlRYdVWeYCWD7PeOA",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InMudmlja2llMTRAZ21haWwuY29tIiwiaWQiOjEsIm9yZyI6ImV4YW1wbGUiLCJyb2xlIjoib3duZXIiLCJleHAiOjE3MjY5MjgzNTR9.jLd5R8sZI37JyTu_S6hxlU3BECz-mv5yxpGalQybR_Y",
            "token_type": "bearer"
        }
        ```

## POST Reset-Password

`http://127.0.0.1:8000/reset-password`

POST Endpoint to reset the user password

- ### Authorization
    Bearer Token

- ### Body
    urlencoded:
    - email: s.vickie14@gmail.com
    - old: password123
    - new: password321
    

- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/reset-password' 
    --data-urlencode 'email=s.vickie14@gmail.com' 
    --data-urlencode 'old=password123' 
    --data-urlencode 'new=password321'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "Password updated successfully"
    }
    ```
    ![password reset mail](assets/password.png)

## POST Invite-Member

`http://127.0.0.1:8000/invite-member`

POST Endpoint which sends an invitation to member
Requires role of owner

- ### Authorization
    Bearer Token

- ### Body
    raw (json):
    ```json
    {
      "email": "testuser@example.com",
      "org": "example",
      "role": "member"
    }
    ```


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/invite-member' 
    --data-raw '{
      "email": "testuser@example.com",
      "org": "example",
      "role": "member"
    }'
    ```

- #### Response
Body:
    ```json
    {
        "message": "Successfully invited testuser@example.com to example"
    }
    ```
    ![invite mail](assets/invite.png)


## GET Create-Member

`http://127.0.0.1:8000/create-member?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIiwib3JnIjoiZXhhbXBsZSIsImludml0ZSI6dHJ1ZSwiZXhwIjoxNzI2OTI4NTQzfQ.SvajApXBnE1D97Mli7gr9mAjBOJfL5fgx-0L7BMLy-U`

GET Endpoint which creates member upon invitation
Generates random default password which is sent to user's email

- ### Query Params

    token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIiwib3JnIjoiZXhhbXBsZSIsImludml0ZSI6dHJ1ZSwiZXhwIjoxNzI2OTI4NTQzfQ.SvajApXBnE1D97Mli7gr9mAjBOJfL5fgx-0L7BMLy-U

- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/create-member?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIiwib3JnIjoiZXhhbXBsZSIsImludml0ZSI6dHJ1ZSwiZXhwIjoxNzI2OTI4NTQzfQ.SvajApXBnE1D97Mli7gr9mAjBOJfL5fgx-0L7BMLy-U'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "Member joined"
    }
    ```
    ![member joined mail](assets/joined.png)

## POST Update-Role

`http://127.0.0.1:8000/update-role`

POST Endpoint to reset the update role
Requires role of owner

- ### Authorization
    Bearer Token

- ### Body
    raw (json):
    ```json
    {
      "email": "testuser@example.com",
      "org": "example",
      "role": "manager"
    }
    ```


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/update-role' 
    --data-raw '{
      "email": "testuser@example.com",
      "org": "example",
      "role": "manager"
    }'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "Member role updated to manager successfully"
    }
    ```

## DELETE Delete-Member

`http://127.0.0.1:8000/delete-member`

POST Endpoint to delete member
Requires role of owner

- ### Authorization
    Bearer Token

- ### Body
    raw (json):
    ```json
    {
      "email": "testuser@example.com",
      "org": "example"
    }
    ```


- #### Request
    cURL:
    ```bash
    curl --location --request DELETE 'http://127.0.0.1:8000/delete-member' 
    --data-raw '{
      "email": "testuser@example.com",
      "org": "example"
    }'
    ```

- #### Response
    Body:
    ```json
    {
        "message": "Member testuser@example.com removed from example successfully"
    }
    ```

## GET Role-Wise-Count

`http://127.0.0.1:8000/role-wise-count?created_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&updated_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&status=1`

GET Endpoint to get statistics for role wise members count
Optional Query Params

- ### Query Params

    - created_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - updated_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - status: 1


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/role-wise-count?created_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&updated_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&status=1'
    ```

- #### Response
    Body:
    ```json
    [
        {
            "role_name": "owner",
            "member_count": 1
        }
    ]
    ```

## GET Org-Wise-Count

`http://127.0.0.1:8000/org-wise-count?created_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&updated_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&status=0`

GET Endpoint to get statistics for organisation wise members count
Optional Query Params

- ### Query Params
    - created_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - updated_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - status: 0


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/org-wise-count?created_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&updated_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&status=0'
    ```

- #### Response
    Body:
    ```json
    [
        {
            "organisation_name": "example",
            "member_count": 1
        }
    ]
    ```

## GET Org-Role-Wise-Count

`http://127.0.0.1:8000/org-role-wise-count?created_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&updated_range=2024-09-14T18:00:00 to 2024-09-14T20:01:00&org_status=0&member_status=1`

GET Endpoint to get statistics for organisation and role wise members count
Optional Query Params

- ### Query Params
    - created_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - updated_range: 2024-09-14T18:00:00 to 2024-09-14T20:01:00
    - org_status: 0
    - member_status: 1


- #### Request
    cURL:
    ```bash
    curl --location 'http://127.0.0.1:8000/org-role-wise-count?created_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&updated_range=2024-09-14T18%3A00%3A00%20to%202024-09-14T20%3A01%3A00&org_status=0&member_status=1'
    ```

- #### Response
    Body:
    ```json
    [
        {
            "organisation_name": "example",
            "role_name": "owner",
            "member_count": 1
        }
    ]
    ```
