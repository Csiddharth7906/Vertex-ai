const rockButton = document.getElementById('rock');
const paperButton = document.getElementById('paper');
const scissorsButton = document.getElementById('scissors');
const resultParagraph = document.getElementById('result');
const computerChoiceParagraph = document.getElementById('computer-choice');

let playerScore = 0;
let computerScore = 0;

function computerChoice() {
    const choices = ['rock', 'paper', 'scissors'];
    return choices[Math.floor(Math.random() * choices.length)];
}

function determineWinner(playerChoice, computerChoice) {
    if (playerChoice === computerChoice) {
        return 'It\'s a tie!';
    } else if ((playerChoice === 'rock' && computerChoice === 'scissors') ||
               (playerChoice === 'scissors' && computerChoice === 'paper') ||
               (playerChoice === 'paper' && computerChoice === 'rock')) {
        playerScore++;
        return 'Player wins!';
    } else {
        computerScore++;
        return 'Computer wins!';
    }
}

function playGame() {
    const playerChoice = this.textContent.toLowerCase();
    const computerChoice = computerChoice();
    const result = determineWinner(playerChoice, computerChoice);
    resultParagraph.textContent = `You chose ${playerChoice}. Computer chose ${computerChoice}. ${result}`;
    computerChoiceParagraph.textContent = `Score - Player: ${playerScore}, Computer: ${computerScore}`;
}

rockButton.addEventListener('click', playGame);
paperButton.addEventListener('click', playGame);
scissorsButton.addEventListener('click', playGame);