USE docker_db;

CREATE TABLE channels (
    id BIGINT NOT NULL,
    name VARCHAR(32) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE channel_types (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(32) NOT NULL,
    user_limit INT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE tmp_channels (
    id BIGINT NOT NULL,
    type_name VARCHAR(32) NOT NULL,
    PRIMARY KEY (id)
);