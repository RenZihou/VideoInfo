# VideoInfo

This is my project (#2) for the summer semester (30240522-3) in Tsinghua University. Mainly focused on wb crawling, web framework and data visualization.

Author: [Ren Zihou](https://github.com/RenZihou)

## Usage

### Run the crawler

Go into the project path and execute command:

```
> .\venv\Scripts\python.exe .\crawler\database.py
> .\venv\Scripts\python.exe .\crawler\bili_crawler_new.py
```

Then your database will be initiated and all the data and images would be stored in `./data`

### Run the web server

```
> .\venv\Scripts\python.exe .\manage.py runserver 0.0.0.0:8000
```

You can visit your web page in browser through `127.0.0.1:8000`

## Develop Progress

### Web Crawling

- [x] video list - 2021/08/30
- [x] video detail - 2021/08/30
- [x] download image - 2021/08/31
- [x] massive data - 2021/09/01

### Web Framework

- [x] framework - 2021/09/01
- [x] list page - 2021/09/01
- [x] detail page - 2021/09/02
- [x] author page - 2021/09/03
- [x] search page - 2021/09/03

### Data Analyse

- [ ] visualization
- [ ] conclusion
