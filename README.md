# Show22_Flipping
## Program to get flipping margins for MLB Show 22

### Description
Like many sports video games (FIFA, Madden, 2K, etc.) MLB the Show has a team-builder mode based around card collecting. These cards, representing current and former players, can be obtained through gameplay, pack openings, or through a community marketplace using the in-game currency 'stubs'. Stubs are earned via gameplay but can be made more efficiently through flipping cards and investing.

This project looks at finding the best flipping margins at any point in time. The following formula represents profit: 0.9 * Sell Value - Buy Value. These profits were converted a margin that was used to drive decisions for flipping targets. A automated the list to be emailed to my personal email each day using Gmail SMTP.

### Drawbacks
The first major drawback was that I wanted to include the trading volume for each card but could not efficiently query each card's recent sales without reaching the request limit for the API. This metric would allow me to add a 'Profit/Minute' metric which would be most helpful for making stubs.
I have also recently discovered a website called showzone.io which has a Flipping tool that is the exact same as mine, complete with the Profit/Minute and all. Regardless I will continue to try and build out my own even after discovering that I am not as inventive as I once thought.

If you happen to come across this and have any questions, comments, tips, or just like MLB the Show as well, feel free to reach me via email at rcpatterson97@gmail.com 
