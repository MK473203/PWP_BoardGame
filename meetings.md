# Meetings notes

## Meeting 1.
* **DATE: 31.1.2024**
* **ASSISTANTS: Mika Oja**

### Minutes

We went through the different sections in the "*RESTful API description*"-wiki page, with Mika making short comments about each one. After reviewing the basic project idea, he recommended focusing on one board game initially to meet project requirements on time. He was doubtful about the safety of sending game rules through the API. However, we were planning from the beginning to make move validation and game rules purely server-side.

Additionally, Mika identified several sections as missing or insufficient, which are outlined below as action points.


### Action points
- Add motivation for our project idea
- Diagram should visualize our project's concepts and their relations, not the system's architecture or endpoints
- Lichess API Client example should be more detailed



## Meeting 2.
* **DATE: 16.2.2024**
* **ASSISTANTS: Mika Oja**

### Minutes

We briefly went through the database design and implementation. Mika noted that our database structure was quite simple and wondered whether we will be able to implement the required amount of resources. 

Additionally, Mika identified several issues in the database design and implementation, which are outlined below as action points.

### Action points
- gameHistory and history should be replaced with a many-to-many relationship between users and games.
- Avoid having to parse frequently accessed- or large quantity of information from strings.
- Add a better way to track turns, that does not depend on large scale string parsing.
- gameTypes should be moved to a table in the database.
- Database population should be done with CLI commands (See Flask API Project Layout in Lovelace)




## Meeting 3.
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Meeting 4.
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Midterm meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




