# backend-assignment

Implement voting REST API for choosing where to go to lunch. Imagine that this API will be consumed by a front-end developer to create UI on top of it. Approach this task as you would approach a real assignment when you are at work. Use this assignment to show us what you care about in terms of code quality, architecture, tests, etc.

Basic business rules/requirements:
1. Everyone can add/remove/update restaurants
2. Every user gets X (hardcoded, but "configurable") votes per
day. Each vote has a "weight". First user vote on the same restaurant counts as 1, second as 0.5, 3rd and all subsequent votes as 0.25.
2.1. If a voting result is the same on multiple restaurants, the winner is the one who got more distinct users to vote on it.
3. Every day vote amounts are reset. Unused previous day votes are lost.
4. Show the history of selected restaurants per time period. For example, the front-end should be able to query which restaurant won the vote on a specific day.
5. Do not forget that frontend dev will need a way to show which restaurants users can vote on and which restaurant is a winner
6. Readme on how to use the API, launch the project, etc.
   
Technologies:
Select what best suits you. Since we use Python with Django, it is preferred. However, feel free to choose other languages/frameworks.
Bonus points (not mandatory):
- Wrapping the app in Docker
- Deploying the API somewhere (for example, Heroku)
