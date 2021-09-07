# VideoInfo

This is my project (#2) for the summer semester (30240522-3) in Tsinghua University. Mainly focused on wb crawling, web framework and data visualization.

Author: [Ren Zihou](https://github.com/RenZihou)

## Usage

### Run the crawler

Go into the project path and execute command:

```
> python .\data\database.py
> python .\crawler\bili_crawler_new.py
```

Then your database will be initiated and all the data and images would be stored in `./data`

### Run the web server

```
> python .\manage.py runserver
```

Then You can visit your web page in browser through `127.0.0.1:8000`

### Plot the graph

```
> python .\analysis\plot.py
```

The results will be saved in `./analysis/output`

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

- [x] visualization - 2021/09/06
- [x] conclusion - 2021/09/07
