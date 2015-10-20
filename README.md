# StreamNotifier_Server

This is the server application for Stream Notifier. It uses SQLAlchemy to update a database based on request from the android app.

The server also starts a 'dispatcher' thread which updates the database based on the twitch api, and sends GCM notifications accordingly.
