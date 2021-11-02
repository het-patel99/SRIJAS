# describing an ec2 instance for web server
resource "aws_instance" "ec2-webserver" {
    # using standard ami and instance type defined in parameters
    ami           = var.ami_id
    instance_type = var.instance_type

    # using the public subnet
    subnet_id     = module.vpc.subnet_public_id

    # predefined key for terraform in AWS
    key_name      = "terraform-key"
    vpc_security_group_ids = [ aws_security_group.ec2-sg.id ]
    associate_public_ip_address = true

    # Assigning name tag
    tags = {
        Name = "SRIJAS-web-server"
    }

    # declaring dependencies
    depends_on = [ module.vpc.vpc_id, module.vpc.igw_id, aws_db_instance.default ]

    # shell script to be run after initializing the server
    /*
        This shell script will install mysql client on web server and add the default address of rds db instance to it's dbdomain file.
        It will install standard LAMP server for PHP, MySQL and Apache services.
        It will install git to clone the repository from the master branch.
        Also other required PHP dependencies
        It will then clone the repository in to /home/ubuntu/project directory
        Create a dynamic parameters.json file for all the dynamically created resources information.
        And move all the web files to /var/www/html where Apache points.
        Finally it will run the sql script stored in Code/Database/Schema directory to initialize the database and populate the default data in it. 
    */
    user_data = <<EOF
#!/bin/sh
sudo apt-get update
sudo apt install -y python3
sudo apt-get install -y mysql-client
echo ${aws_db_instance.default.address} >/tmp/dbdomain.txt
sudo mv /tmp/dbdomain.txt /dbdomain.txt
#!/bin/bash
sudo apt update -y
sudo apt install lamp-server^ -y
sudo systemctl start apache2
sudo apt install git-all -y
sudo apt install curl
sudo apt install php-cli
sudo apt install php-mbstring -y
cd ~
curl -sS https://getcomposer.org/installer -o composer-setup.php
HASH=756890a4488ce9024fc62c56153228907f1545c228516cbf63f885e036d37e9a59d27d63f46af1d4d07ee0f76181c7d3
sudo php composer-setup.php --install-dir=/usr/local/bin --filename=composer
cd /home/ubuntu
mkdir project
cd project
git clone https://github.com/hvudeshi/SRIJAS.git
sudo chown -R ubuntu:ubuntu SRIJAS/
cd SRIJAS/Code
echo '{"server_name" : "${aws_db_instance.default.address}", "user_name":"${var.db_user_name}", "password": "${var.db_password}", "db_name": "${aws_db_instance.default.name}", "email_password": "${var.email_password}"}' > Web_app/parameters.json
sudo cp -a Web_app/. /var/www/html/
cd /
sudo chmod -R 777 /var/www/html
cd /
mysql -u ${var.db_user_name} -h ${aws_db_instance.default.address} --password=${var.db_password} < /home/ubuntu/project/SRIJAS/Code/Database/schema/srijas.sql
cd /var/www/html
php test.php
EOF
}

# describing an ec2 instance for scrapping server
resource "aws_instance" "ec2-scrapper" {
    # using standard ami and instance type defined in parameters
    ami           = var.ami_id
    instance_type = var.instance_type

    # using the public subnet
    subnet_id     = module.vpc.subnet_public_id

    # predefined key for terraform in AWS
    key_name      = "terraform-key"
    vpc_security_group_ids = [ aws_security_group.ec2-sg.id ]
    associate_public_ip_address = true

    # Assigning name tag
    tags = {
        Name = "SRIJAS-scrapping-server"
    }

    # declaring dependencies
    depends_on = [ module.vpc.vpc_id, module.vpc.igw_id, aws_db_instance.default ]

    # shell script to be run after initializing the server
    /*
        This shell script will install zip, python3, libnss3, python3-pip, python3-virtualenv and git.
        It will create a virtual environment and install all the required packages from requirements.txt.
        It will get the latest chromedriver and stable chrome version for selenium automation.
        It will then clone the repository in to /home/ubuntu/project directory
        Create a dynamic parameters.json file for all the dynamically created resources information.
        It will also schedule the execution of the scrapping files to daily execution at a given time. 
    */
    user_data = <<EOF
#!/bin/sh
sudo apt update
sudo apt-get install -y zip unzip 
sudo apt install -y python3
sudo apt install -y unzip libnss3 python3-pip 
sudo apt install python3-virtualenv -y
sudo apt install git-all -y 
cd /tmp
sudo wget https://chromedriver.storage.googleapis.com/94.0.4606.61/chromedriver_linux64.zip
sudo unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
chromedriver --version
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb 
google-chrome-stable --version
cd /home/ubuntu
mkdir project
cd project
git clone https://github.com/hvudeshi/SRIJAS.git
cd SRIJAS/Code
echo '{"server_name" : "${aws_db_instance.default.address}", "user_name":"${var.db_user_name}", "password": "${var.db_password}", "db_name": "${aws_db_instance.default.name}", "linked_in_pwd":"SRIJASGMAILPWD"}' > Scrapper/parameters.json
virtualenv -q -p /usr/bin/python3.8 $1
source $1/bin/activate
$1/bin/pip install -r /home/ubuntu/project/SRIJAS/requirements.txt
echo "30 1 * * * python3 /home/ubuntu/project/SRIJAS/Code/Scrapper/Scrapper.py" | crontab -
crontab -l | { cat; echo "30 1 * * * python3 /home/ubuntu/project/SRIJAS/Code/Scrapper/scrapper_glassdoor.py"; } | crontab -
EOF
}

# describing the security group for ec2 instances
resource "aws_security_group" "ec2-sg" {
  name        = "security-group"
  description = "allow inbound access to the EC2 instance"

  # using the vpc created earlier for this security group
  vpc_id      = module.vpc.vpc_id

  # allowing all inbound and outbound traffic for ec2 instances.
  ingress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}
