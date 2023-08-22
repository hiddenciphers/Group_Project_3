FROM python:3.9
EXPOSE 8501
WORKDIR /app

ARG url
ARG smartContractAddress
ARG pinataApi
ARG pinataApiSecret

ENV WEB3_RPC=$url
ENV SMART_CONTRACT_ADDRESS=$smartContractAddress
ENV PINATA_API_KEY=$pinataApi
ENV PINATA_SECRET_API_KEY=$pinataApiSecret

RUN pip3 install --upgrade pip 

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

 

COPY . .

CMD streamlit run ./src/skillified.py