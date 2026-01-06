create database routineloaddb
use routineloaddb

CREATE TABLE cfx_work_completed (
    MessageID varchar(255),
    receiveat DATETIME,

    MessageType varchar(255),
    MessageVersion INT,
    MessageTime DATETIME,
    Sender varchar(255),
    
    `Data` String, -- 存储整个 Data JSON 作为备份
    
    processed_time String,
    device_id varchar(255),
    line_id varchar(255),
    mfg_plant_code varchar(255),
    factory varchar(255),
    message_name varchar(255),
    source varchar(255),

    rawdata String, -- 存储 RawData JSON 作为备份
    
    RawData_message_name varchar(255),
    RawData_version varchar(255),
    RawData_timestamp String,
    RawData_UniqueID varchar(255),
    RawData_source varchar(255),
    RawData_target varchar(255),
    RawData_RequestID varchar(255),

    RawData_MessageBody_type varchar(255),
    RawData_MessageBody_TransactionID varchar(255),
    RawData_MessageBody_Result varchar(255),
    RawData_MessageBody_PrimaryIdentifier varchar(255),
    
    RawData_MessageBody_HermesIdentifier varchar(255),
    RawData_MessageBody_UnitCount INT
)
DUPLICATE KEY (MessageID)
DISTRIBUTED BY HASH(MessageID) BUCKETS 4
PROPERTIES (
    "replication_num" = "1"
);




-- 2. Create the routine load (without the DUPLICATE KEY clause)
Create  ROUTINE LOAD cfx_routine_load
ON cfx_work_completed
COLUMNS TERMINATED BY ",",
COLUMNS (
    MessageID ,                   -- This should match Kafka's key "MessageID"
    receiveat ,                    -- This should match Kafka's key "receiveat"
    MessageType ,                -- This should match Kafka's key "MessageType"
    MessageVersion ,          -- This should match Kafka's key "MessageVersion"
    MessageTime ,                -- This should match Kafka's key "MessageTime"
    Sender ,
    `Data`,  -- Store `Data` as a backup
    processed_time = JSON_EXTRACT(`Data`, '$.ProcessedTime'),
    device_id = JSON_EXTRACT(`Data`, '$.Meta.DeviceID'),
    line_id = JSON_EXTRACT(`Data`, '$.Meta.LineID'),
    mfg_plant_code = JSON_EXTRACT(`Data`, '$.Meta.MfgPlantCode'),
    factory = JSON_EXTRACT(`Data`, '$.Meta.Factory'),
    message_name = JSON_EXTRACT(`Data`, '$.Meta.MessageName'),
    source = JSON_EXTRACT(`Data`, '$.Meta.Source'),
    rawdata,
    RawData_message_name = JSON_EXTRACT(`Data`, '$.RawData.MessageName'),
    RawData_version = JSON_EXTRACT(`Data`, '$.RawData.Version'),
    RawData_timestamp = JSON_EXTRACT(`Data`, '$.RawData.TimeStamp'),
    RawData_UniqueID = JSON_EXTRACT(`Data`, '$.RawData.UniqueID'),
    RawData_source = JSON_EXTRACT(`Data`, '$.RawData.Source'),
    RawData_target = JSON_EXTRACT(`Data`, '$.RawData.Target'),
    RawData_RequestID = JSON_EXTRACT(`Data`, '$.RawData.RequestID'),
    RawData_MessageBody_type = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.$type'),
    RawData_MessageBody_TransactionID = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.TransactionID'),
    RawData_MessageBody_Result = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.Result'),
    RawData_MessageBody_PrimaryIdentifier = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.PrimaryIdentifier'),
    RawData_MessageBody_HermesIdentifier = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.HermesIdentifier'),
    RawData_MessageBody_UnitCount = JSON_EXTRACT(`Data`, '$.RawData.MessageBody.UnitCount')
)
PROPERTIES(
    "format"="json"
)
FROM KAFKA(
    "kafka_broker_list" = "10.136.218.207:9092",
    "kafka_topic" = "CFX_CFX_Production_WorkCompleted",
    "property.kafka_default_offsets" = "OFFSET_BEGINNING"
);



ALTER TABLE cfx_work_completed MODIFY COLUMN Data String;


SHOW ROUTINE LOAD FOR routineloaddb.cfx_routine_load
STOP ROUTINE LOAD FOR  routineloaddb.cfx_routine_load;