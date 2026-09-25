# SkillSwap

SkillSwap is a student-to-student skill exchange platform. Students can publish what they know, discover campus skills, and send requests to learn together.

## Features

- Home page with featured skills and calls to action
- Searchable, filterable skill directory
- Skill detail pages with teach/learn information and portfolio images
- Validated add-skill form with local uploads (5 MB limit)
- Exchange request workflow with pending, accepted, and rejected states
- Local JSON persistence for a zero-setup demo
- Repository and storage abstractions ready for DynamoDB and S3
- Responsive desktop, tablet, and mobile layout

## Technology

Python, Flask, Jinja2, vanilla JavaScript, CSS, boto3, and python-dotenv.

## Local setup

```text
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. The app listens on `HOST` and `PORT`; set `HOST=0.0.0.0` when running on an EC2 instance.

## Project structure

- `app.py`: application factory and routes
- `config.py`: environment-driven configuration
- `models/`: small dataclasses for skills and requests
- `repositories/`: local JSON repositories and DynamoDB repository implementations
- `services/`: validation, business logic, and local/S3 storage services
- `templates/`: Jinja pages
- `static/`: CSS and JavaScript
- `data/`: generated local JSON data (ignored by Git)
- `uploads/`: local portfolio images (ignored by Git)

## Configuration and local mode

Copy `.env.example` to `.env`. Local mode is the default and requires no AWS account or credentials. Seed skills are created in `data/skills.json`; new skills and requests are written there so a demo survives a restart. Uploaded portfolio files are saved under `uploads/`.

The app never contains AWS credentials. boto3 uses its normal credential provider chain, which means an EC2 IAM role can be used later without changing source code.

## AWS path

The planned deployment is:

```text
Browser -> EC2 Flask app -> DynamoDB (skills and requests)
                     \-> S3 (portfolio images)
```

`DynamoDBSkillRepository`, `DynamoDBRequestRepository`, and `S3StorageService` are included as clear integration points. To complete the AWS switch, wire these implementations in `create_app` when `STORAGE_MODE=aws`, provision the two DynamoDB tables with `id` as the partition key, and give the EC2 instance profile access to those tables and the S3 bucket. No access keys belong in `.env` or source code.

For an Amazon Linux EC2 deployment, install Python and the requirements, copy the project and a production `.env`, set `HOST=0.0.0.0`, configure the IAM role, and run behind Gunicorn and a reverse proxy such as Nginx. Open only the required HTTP/HTTPS security-group ports.

## Security notes

- Keep `.env` out of version control and use a strong production `SECRET_KEY`.
- Use IAM roles rather than AWS access keys on EC2.
- Uploaded filenames are sanitized and generated names prevent collisions.
- Upload size and image extensions are checked server-side.
- Jinja auto-escaping protects rendered user content.
- Add CSRF protection and authentication before a public production launch.