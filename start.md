1. 安装必要的软件

```bash
sudo apt install python3
sudo apt install mysql-server
```

2. 安装库

```bash
pip install flask
pip install pymysql
```

3. 配置mysql

```bash
sudo mysql_secure_installation #初始化数据库，全部选择y
sudo systemctl start mysqld
sudo systemctl enable mysqld
sudo mysql #进入数据库命令行
```

4. 创建数据库和用户

```sql
CREATE DATABASE wm;
CREATE USER 'wm'@'localhost' IDENTIFIED BY 'wm123!@#';
GRANT ALL PRIVILEGES ON wm.* TO 'wm'@'localhost';
FLUSH PRIVILEGES;
```

5. 导入数据库模板

```sql
use wm;
```

```sql

drop table user;
drop table dict;
drop table word;
drop table game;

create table user(
    id int primary key auto_increment,
    username varchar(255),
    pwhash varchar(255),
    introduction varchar(255),
    rating int,
    type varchar(255),
    deleted boolean
);

create table dict(
    id int primary key auto_increment,
    dictname varchar(255),
    deleted boolean
);

create table word(
    id int primary key auto_increment,
    dictid int,
    english varchar(255),
    chinese varchar(255),
    deleted boolean
);

create table game(
    id int primary key auto_increment,
    ownerid int,
    dictid int,
    users text,
    wordlist text,
    result text,
    perf int,
    status int
);
```