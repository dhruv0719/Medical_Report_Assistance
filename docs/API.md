# API Reference Documentation
## Medical Report Assistant — Backend Endpoints

This document outlines the API endpoints, authentication mechanisms, request payloads, and response formats for the Medical Report Assistant backend.

---

### 1. General API Information

*   **Base URL:** `http://127.0.0.1:8000/api/v1` (Local Development)
*   **Content Type:** `application/json` (except file uploads and login which require `multipart/form-data`)
*   **Authentication:** Bearer Token (JWT). Authenticated requests must include the header:
    ```http
    Authorization: Bearer <your_jwt_access_token>
    ```

---

### 2. Global Error Codes

When a request fails, the API returns a standard HTTP status code and a JSON response detailing the error:

```json
{
  "detail": "Detailed description of the error."
}
```

*   `400 Bad Request`: Incorrect input parameters, invalid formats, or failed validations.
*   `401 Unauthorized`: Missing, expired, or invalid JWT token.
*   `403 Forbidden`: Insufficient permissions to access the resource.
*   `404 Not Found`: The requested resource could not be found.
*   `422 Unprocessable Entity`: Data validation failed (FastAPI standard).
*   `500 Internal Server Error`: Server encountered an unexpected exception during execution.

---

### 3. Endpoint Specifications

#### 3.1 Health Check
Check the API server status.

*   **URL:** `/health`
*   **Method:** `GET`
*   **Auth Required:** No
*   **Response:**
    *   `200 OK`
        ```json
        {
          "status": "ok"
        }
        ```

---

#### 3.2 Authentication & Registration

##### 3.2.1 User Login
Authenticates user credentials and returns a JWT access token.

*   **URL:** `/auth/jwt/login`
*   **Method:** `POST`
*   **Auth Required:** No
*   **Content Type:** `application/x-www-form-urlencoded` or `multipart/form-data`
*   **Request Body:**
    *   `username` (string, required): The user's email address.
    *   `password` (string, required): The user's password.
*   **Response:**
    *   `200 OK`
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```
    *   `400 Bad Request`
        ```json
        {
          "detail": "Incorrect username or password"
        }
        ```

##### 3.2.2 User Registration
Registers a new user account.

*   **URL:** `/auth/register`
*   **Method:** `POST`
*   **Auth Required:** No
*   **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "strongpassword123",
      "is_active": true,
      "is_superuser": false,
      "is_verified": false
    }
    ```
*   **Response:**
    *   `201 Created`
        ```json
        {
          "id": 1,
          "email": "user@example.com",
          "is_active": true,
          "is_superuser": false,
          "is_verified": false
        }
        ```
    *   `400 Bad Request`
        ```json
        {
          "detail": "REGISTER_USER_ALREADY_EXISTS"
        }
        ```

##### 3.2.3 User Logout
Logs out the current user and invalidates the session token.

*   **URL:** `/auth/logout`
*   **Method:** `POST`
*   **Auth Required:** Yes
*   **Response:**
    *   `204 No Content` (No response body)

##### 3.2.4 Request Password Reset Token
Sends a password reset token via configured email channels (logged locally in console during development).

*   **URL:** `/auth/forgot-password`
*   **Method:** `POST`
*   **Auth Required:** No
*   **Request Body:**
    ```json
    {
      "email": "user@example.com"
    }
    ```
*   **Response:**
    *   `202 Accepted`
        ```json
        {}
        ```

##### 3.2.5 Reset Password
Resets the password using a token received in `/auth/forgot-password`.

*   **URL:** `/auth/reset-password`
*   **Method:** `POST`
*   **Auth Required:** No
*   **Request Body:**
    ```json
    {
      "token": "reset_token_received",
      "password": "newsecurepassword123"
    }
    ```
*   **Response:**
    *   `200 OK`
        ```json
        {}
        ```

---

#### 3.3 User Management

##### 3.3.1 Get Current User Profile
Retrieves the logged-in user's details.

*   **URL:** `/users/me`
*   **Method:** `GET`
*   **Auth Required:** Yes
*   **Response:**
    *   `200 OK`
        ```json
        {
          "id": 1,
          "email": "user@example.com",
          "is_active": true,
          "is_superuser": false,
          "is_verified": false
        }
        ```

##### 3.3.2 Update Current User Profile
Updates details of the logged-in user.

*   **URL:** `/users/me`
*   **Method:** `PATCH`
*   **Auth Required:** Yes
*   **Request Body:**
    ```json
    {
      "email": "newemail@example.com",
      "password": "changedpassword321"
    }
    ```
*   **Response:**
    *   `200 OK`
        ```json
        {
          "id": 1,
          "email": "newemail@example.com",
          "is_active": true,
          "is_superuser": false,
          "is_verified": false
        }
        ```

---

#### 3.4 Medical Report Analysis

##### 3.4.1 Analyze Medical Report File
Accepts a PDF/TXT medical lab report, extracts structured test data, runs safety triage, retrieves RAG reference context, drafts explanations, and returns the results.

*   **URL:** `/analysis/analyze-report`
*   **Method:** `POST`
*   **Auth Required:** Yes
*   **Content Type:** `multipart/form-data`
*   **Request Parameter:**
    *   `file` (file binary, required): The PDF or TXT report file.
*   **Response:**
    *   `202 Accepted`
        ```json
        {
          "filename": "cbc_report_mild_anemia.pdf",
          "file_hash": "e99a182eb0b0374b5c8188e6a243e3ff7cf830c2d377b084931a729e2fcf0014",
          "extraction": {
            "text_length": 1420,
            "method": "text",
            "pages": 1
          },
          "parsed": {
            "patient_id": "MRN-92831",
            "report_date": "2026-05-15",
            "report_type": "Complete Blood Count",
            "lab_name": "Quest Diagnostics",
            "tests": [
              {
                "name": "hemoglobin",
                "value": "11.2",
                "unit": "g/dL",
                "reference_range": "13.0-17.0",
                "is_abnormal": true,
                "status": "abnormal_low",
                "flag": "L",
                "timestamp": null
              },
              {
                "name": "wbc",
                "value": "6.5",
                "unit": "x10³/µL",
                "reference_range": "4.0-11.0",
                "is_abnormal": false,
                "status": "normal",
                "flag": null,
                "timestamp": null
              },
              {
                "name": "platelet",
                "value": "250",
                "unit": "x10³/µL",
                "reference_range": "150-400",
                "is_abnormal": false,
                "status": "normal",
                "flag": null,
                "timestamp": null
              }
            ],
            "impression": "Mild microcytic anemia, suspect iron deficiency. Recommend follow-up iron panel.",
            "metadata": {
              "parsed_at": "2026-05-25T09:44:10.123456"
            }
          },
          "triage": {
            "overall_urgency": "moderate",
            "alerts": [
              {
                "level": "moderate",
                "category": "ABNORMAL_VALUE",
                "test_name": "hemoglobin",
                "value": "11.2",
                "unit": "g/dL",
                "threshold": "13.0-17.0",
                "message": "hemoglobin value of 11.2 g/dL is lower than normal range (13.0-17.0)",
                "action_required": "Schedule routine medical consultation",
                "urgency": "MODERATE"
              },
              {
                "level": "info",
                "category": "INFORMATION",
                "test_name": "wbc",
                "value": "6.5",
                "unit": "x10³/µL",
                "threshold": "4.0-11.0",
                "message": "wbc is within normal range",
                "action_required": "No action needed",
                "urgency": "ROUTINE"
              },
              {
                "level": "info",
                "category": "INFORMATION",
                "test_name": "platelet",
                "value": "250",
                "unit": "x10³/µL",
                "threshold": "150-400",
                "message": "platelet is within normal range",
                "action_required": "No action needed",
                "urgency": "ROUTINE"
              }
            ],
            "next_steps": [
              "📞 Schedule an appointment with your healthcare provider within the week",
              "Discuss these findings at your next visit",
              "📋 Bring this report to your doctor appointment",
              "💬 Write down any questions you have for your doctor",
              "\n📝 Specific Recommendations:",
              "\nFor hemoglobin:",
              "  • Consider iron-rich foods (red meat, spinach, beans)",
              "  • Ask your doctor about iron supplements",
              "  • May need additional tests: iron studies, vitamin B12, folate"
            ]
          },
          "explanations": {
            "hemoglobin": {
              "text": "According to MedlinePlus guidelines, Hemoglobin is a protein in your red blood cells that carries oxygen from your lungs to the rest of your body.\n\nYour hemoglobin value is 11.2 g/dL, which is low compared to the normal range of 13.0-17.0 g/dL. A low hemoglobin level is called anemia.\n\nCommon causes of low hemoglobin include iron deficiency, vitamin deficiencies, or bleeding. Your doctor can help determine the exact cause.\n\nYou should consult your doctor to discuss this result. They may recommend dietary changes, iron supplements, or further blood tests.\n\n⚠️ IMPORTANT: This explanation is for informational purposes only. It does not constitute medical advice. Always consult your healthcare provider for interpretation of your specific results.",
              "sources": [
                "MedlinePlus (NIH)"
              ],
              "is_abnormal": true,
              "is_critical": false
            }
          },
          "session_id": "4b7b25e7-6fe3-441b-a5d6-0c1a79f18228",
          "processing_time": 4.12
        }
        ```
    *   `401 Unauthorized` (Token missing or expired)
    *   `400 Bad Request` (Unsupported file type, file size too large, or OCR failure)
        ```json
        {
          "detail": "File validation failed: Unsupported file type: png"
        }
        ```
    *   `500 Internal Server Error`
        ```json
        {
          "detail": "An error occurred during analysis: [Error details]"
        }
        ```
