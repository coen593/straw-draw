# Straw Draw
## Drawing straws to settle who does what, wherever you are
## CS50x 2021 Final Project
[Link to video](https://youtu.be/scVNbviV9sw)

## Description
Straw Draw is an application that allows users to draw straws to settle who needs to do something. Imagine a family or a group of friends or roommates discussing (and not agreeing) in their chat group who needs to do the groceries or run some other errant. Straw Draw allows them to quickly settle this by having the group enter their name in the app, and have the app randomly select one or more person/people to run the errant. 
The way this works: one person creates a "draw" by entering their name, email, number of "short straws" (i.e. how many people need to be selected) and enters a name for the draw. The app then provides a easily copyable and shareable link that the creator can provide to the other participants. The other participants enter their details, and once completed, the creator triggers the draw and the Straw Draw app selects one or more people randomly. Email notifications are a part of this too. Email notifications are sent to the creator when (s)he creates a draw, to participants when they register for a draw, and to all participants after a draw is triggered to inform them of the result.
Straw Draw runs on Python as a Flask application in the back end, while using HTML, CSS and a little bit of JavaScript for the front end. The database is managed using SQLite. The application was developed in VS Code

## Configuration instructions
Make sure to set the mail username and password in your environment when trying to run. Mail config is set up for Gmail at the beginning of app.py.

## Installation instructions
1. Clone the code
2. Install all dependencies as specified in the requirements.txt file
3. Set up email following configuration instructions.
4. Run command `python -m flask run`

## Design choices
Straw Draw is implemented as a mobile first but responsive website. Moreover, throughout the process, no permanent account is made for a user, only temporary accounts associated with a single draw. The reason for this is that from a user perspective, setting up and participating in a draw should be a quick thing, without hassle. For this reason, no downloading of an application or proper registering is implemented. Users navigating the website do get a session - this is instead based on the draw in which they participate.

## File explanation: python files
This project contains three python files: app.py, helpers.py and mailBodys.py.

### app.py
app.py forms the core of the application from which everything runs. After importing the necessary libraries and functions, configuring the mail application and setting up the database connections, the various application routes are defined and specified. Apart from redirecting and rendering, the routes mostly insert into or query the database.

#### index
The index route simply triggers the homepage.

#### create
The create route centers around the create.html template which is rendered when the route is called through a GET request. When called through POST, the requests variables are checked and entered into the database, triggering a confirmation email too.

#### participate
The participate route centers around the participate.html template which is rendered when the route is called through a GET request. If no code is provided in the GET request, a special template participate-new is rendered instead, with a form in which the user can submit a code. The code coming from the GET request is checked against the database before returning the template (in case of error the apology template is rendered). 
When called through POST, the requests variables are checked and entered into the database, triggering a confirmation email too.

#### manage
When called through a GET request, depending on whether a session is active and/or a code/email combination is provided, either a code/email combination is requested to the user, or the manage.html template is rendered. 
When called through POST, either a participant is deleted (removed from draw and db in general) or a draw is triggered. In case of the latter, several participants are chosen at random from the draw (using the randint function) and flagged in the db as selected. The app then returns the selected template to the creator showing the result. All participants receive an email confirmation too. If this draw is checked by any user in manage afterwards, they'll see this result instead of the usual manage template.

#### other routes
The delete route removes a participant from a draw by removing from the participants table.
The other route clears a session and then returns the homepage.
The route howdoesitwork returns the howdoesitwork template.

### helpers.py
Two functions are defined here: login_required, which checks whether a session is currently ongoing and is necessary to trigger the delete function, and apology, which renders an apology template in case of user errors.

### mailBodys.py
Bodies for the emails sent are defined here, using HTML.

## File explanation: draw.db database
Data is managed through SQLite in the draw.db database. The database consists of three tables.

### DB table: creators
Creators is used to define each individual draw. It has columns for a unique id, person_id (linking to persons table), code (used to navigate to the draw), straws (how many people are to be selected in the draw), createdt (when is the draw created, timetamps) and triggerdt( when is the draw triggered, timestamp).

### DB table: participants
Every participant is stored here. It has columns for a unique id, number (indicating the participant number in a specific draw), person_id (linking to persons table), selected (boolean indicating whether or not participant is selected) and creator_id (linking to the id in creators).

### DB table: persons
To store personal data. Apart from a unique id, it contains a name and email for each person. The app ensures no duplicates are entered.

## File explanation: templates
Various templates are rendered through the app's routes.

### layout.html
Sets the layout for each of the other templates. Most important is the Navbar, created using Bootstrap. The navbar contains the logo of the app as well as various links - the links are dependent on whether a session is currently active or not.

### index.html
Home page. Contains three links to create a draw, participate in a draw or manage a draw when no session is active. When a session is active, there is only the option to manage a draw or to do "another draw" - the latter ends the session and then redirects again to index.

### apology.html
Contains a simple error message with customised text whenever a user triggered error comes up.

### howdoesitwork.html
A simple text page with no further links or forms, explaining how the app works.

### create.html
Shows the user a form where to submit the details of their draw to be created. The template contains some JavaScript in the form of a plus and minus button used to enter the number of straws.

### participate-new.html
When the participate route is called by a GET request but no code is provided, this HTML template shows up. It asks the user for a code and then triggers another GET request to the participate route.

### participate
When the participate route is called by a GET request and a code is provided in the request, this HTML template shows, showing the user a form in which they submit their details to be a participant in a draw.

### manage-new.html
When the manage route is called by a GET request but no code is provided AND currently no session is active, this HTML template shows up. It asks the user for a code and email address and then triggers another GET request to the manage route.

### manage.html
When the manage route is called by a GET request and a session is active or a correct code/email combination is submitted, and the draw has never been triggered, this HTML template shows up. If the user is NOT the creator, it simply shows a list of participants in the current draw, and a button to copy the link to share with other new participants to register. If the user is the creator, in addition to the above, the user has the option to remove participants from the draw with a red X button, and can trigger the draw by a button.

### select.html
When the manage route is called by a GET request and a session is active or a correct code/email combination is submitted, **and the draw has been triggered** (based on the triggerdt in the creators table), this template shows. It shows a list of all the people selected in the draw.

## File explanation: other
In the static folder, styles.css contains all the css code used for the templates. An image "DeleteCross.png" is provided and is rendered on the manage page if the current session belongs to the draw's creator.

## License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)