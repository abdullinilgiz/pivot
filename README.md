# PIVOT
### Description
Simple social platform called 'Pivot' where users can share their own diaries.
### TechStack
Python3.10
Django 4.2.3
DRF 3.14.0
Pillow 10.0.0
djoser 2.2.0g
### Author
Ilgiz Abdullin
### Installation
Clone this repository to your working folder:
```
git clone git@github.com:abdullinilgiz/pivot.git
```
Enter directory
```
cd pivot
```
Create and activate virtual environment:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
Install all dependencies from requirement.txt:
```
pip install -r requirements.txt
```
Make migrations:
```
cd pivot
python3 manage.py migrate
```
Run the code:
```
python3 manage.py runserver
```
## API for Pivot project
API uses endpoints, that start with:
```
/api/v1/
```
### API requests examples
Following request return list of all posts
```
GET api/v1/posts/
```
The next request create post entity
```
POST api/v1/posts/
```
With payload:
```
{
  "text": "string",
  "image": "string",
  "group": 0
}
```