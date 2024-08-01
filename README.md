## Build Environment Preparation

```commandline
brew install pyenv
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
pyenv install 3.10.0
pyenv local 3.10.0
pip install poetry
poetry config virtualenvs.in-project true
poetry install
```

## How to add Dependencies 
```commandline
poetry add "fastapi~=0.111.0"
poetry add "websocket-client~=1.8.0"
poetry add "python-dotenv~=1.0.1"
poetry add "python-uvicorn"
```

## Run the Script
#### 1. Run Python directly
```commandline
poetry install
poetry run server
```

## Start Application Using Docker
```commandline
docker-compose up --build -d
```

## Curl Command
#### 1. Get Api for Optin (will provide available port and host)
```commandline
curl -i -X GET 'http://localhost:3002/stream/optin/1234534'
```
#### 1. Post Api for OptOut 
```commandline
curl -i -X POST \
   -H "Content-Type:application/json" \
   -d \
'{
   "callId":"1234534",
   "host":"192.168.31.100",
   "port":5940
}' \
 'http://localhost:3002/stream/optout'
```