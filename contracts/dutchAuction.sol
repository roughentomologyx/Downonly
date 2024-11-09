// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DutchAuction {
    address public owner;
    uint256 public startTime;
    uint256 public startingPrice;
    uint256 public minPrice;
    uint256 public decreasingDuration;
    uint256 public secondsAtBottom;
    uint256 public cooldown;       // Now set in constructor
    uint256 public initialPause;   // New variable for initial pause
    uint256 public nextAuctionTime;
    uint256 public nextMintID = 1;
    bool public ended = false;
    bool public auctionCycleActive = false;
    bool public emergencyPaused = false;
    uint256 public epauseStartTime;

    string[] public characters = ["business", "astronaut", "knight", "clown", "chef", "police", "ski", "construction", "farm", "bath", "judge"];
    string[] public obstacles = ["shoppingcart", "balloons", "satellite", "toilet", "books", "horse", "snowCannon", "piano", "stove", "money", "transporter"];
    string[] public surfaces =  ["antenna", "livingRoom", "windPark", "court", "castle", "ferris", "scaffolding", "cruise", "snowPark", "victoryColumn", "escalator"];

    mapping(string => uint8) public assetUsageCount;

    event AuctionSale(
        address buyer,
        uint256 amount,
        uint256 price,
        uint256 mintID,
        string character,
        string obstacle,
        string surface
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can call this function");
        _;
    }

    modifier auctionNotEnded() {
        require(
            auctionCycleActive && (!ended || block.timestamp >= nextAuctionTime),
            "Auction has ended or not yet started"
        );
        _;
    }

    constructor(
        uint256 _startingPrice,
        uint256 _minPrice,
        uint256 _secondsAtBottom,
        uint256 _decreasingDuration,
        uint256 _cooldown,         // Added cooldown as a constructor parameter
        uint256 _initialPause      // Added initialPause as a constructor parameter
    ) {
        require(_startingPrice > _minPrice, "Starting price should be greater than minimum price.");
        owner = msg.sender;
        startingPrice = _startingPrice;
        minPrice = _minPrice;
        secondsAtBottom = _secondsAtBottom;
        decreasingDuration = _decreasingDuration;
        cooldown = _cooldown;
        initialPause = _initialPause;
        startTime = block.timestamp;
        nextAuctionTime = 0;
    }

    function currentPrice() public view returns (uint256) {
        uint256 elapsed = block.timestamp - startTime;
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 timeInCycle = elapsed % cycleDuration;

        if (timeInCycle < decreasingDuration) {
            uint256 priceDrop = startingPrice - minPrice;
            return startingPrice - (priceDrop * timeInCycle / decreasingDuration);
        } else {
            return minPrice;
        }
    }

    function startAuctionCycle() external onlyOwner {
        require(!auctionCycleActive, "Auction cycle is already active");
        auctionCycleActive = true;
        startTime = block.timestamp + initialPause;  // Use initialPause variable
        nextAuctionTime = startTime;
    }

    function endAuctionCycle() external onlyOwner {
        require(auctionCycleActive, "Auction cycle is not active");
        auctionCycleActive = false;
        ended = true;
        nextAuctionTime = 0;
    }

    function buy(
    string memory character,
    string memory obstacle,
    string memory surface
) external payable auctionNotEnded {
    require(!emergencyPaused, "The contract is in emergency pause");
    require(
        containedIn(character, characters) && assetUsageCount[character] < 3,
        "Invalid or depleted character choice"
    );
    require(
        containedIn(obstacle, obstacles) && assetUsageCount[obstacle] < 3,
        "Invalid or depleted obstacle choice"
    );
    require(
        containedIn(surface, surfaces) && assetUsageCount[surface] < 3,
        "Invalid or depleted surface choice"
    );

    uint256 price = currentPrice();
    require(msg.value >= price, "Bid amount is lower than the current price");


    assetUsageCount[character]++;
    assetUsageCount[obstacle]++;
    assetUsageCount[surface]++;
    nextAuctionTime = block.timestamp + cooldown;
    startTime = nextAuctionTime;
    uint256 mintID = nextMintID++;
    emit AuctionSale(msg.sender, msg.value, price, mintID, character, obstacle, surface);


    uint256 refundAmount = msg.value - price;
    if (refundAmount > 0) {
        (bool success, ) = payable(msg.sender).call{value: refundAmount}("");
        require(success, "Refund failed");
    }
}


    function emergencyPause() external onlyOwner {
        require(auctionCycleActive && !ended, "Auction must be active and not ended");

        if (emergencyPaused) {
            // Resuming from emergency pause
            emergencyPaused = false;

            // Calculate how long the contract was paused
            uint256 epauseDuration = block.timestamp - epauseStartTime;

            // Adjust the timers to resume from the point where they left off
            startTime += epauseDuration;
            nextAuctionTime += epauseDuration;

        } else {
            emergencyPaused = true;
            // Record the current time to calculate pause duration later
            epauseStartTime = block.timestamp;
        }
    }

    function containedIn(string memory value, string[] memory array) internal pure returns (bool) {
        for (uint256 i = 0; i < array.length; i++) {
            if (
                keccak256(abi.encodePacked(value)) ==
                keccak256(abi.encodePacked(array[i]))
            ) {
                return true;
            }
        }
        return false;
    }

    function withdraw() external onlyOwner {
        require(ended, "Auction must be ended to withdraw");
        payable(owner).transfer(address(this).balance);
    }

    function onCooldown() public view returns (bool) {
        return block.timestamp < nextAuctionTime;
    }

    // Tells how many seconds during a big auction cycle (one buy to next) has elapsed
    function elapsed() public view returns (uint256) {
        require(!emergencyPaused, "Emergency pause active");
        return block.timestamp - startTime;
    }

    // Tells how many seconds during a small auction cycle (one price decrease cycle) has elapsed
    function timeInCycle() public view returns (uint256) {
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        return elapsed() % cycleDuration;
    }



    // Auction phases:
    // - auctionNotStarted (premint): auction not started yet
    // - auctionActive (mint): auction is running and has not ended and is not on cooldown or emergency paused
    // - auctionsEnded (postmint): only after the auction has ended is this activated
    // - auctionCooldown: after buy or after start, a short amount of time paused
    // - emergencyPause: manual halt of auction with timers resuming where they left off
    function getPhase() public view returns (string memory) {
        if (emergencyPaused) {
            return "emergencyPause";
        }
        if (!auctionCycleActive && !ended) {
            return "auctionNotStarted";
        } else if (!auctionCycleActive && ended) {
            return "auctionsEnded";
        } else if (onCooldown() && auctionCycleActive) {
            return "auctionCooldown";
        } else if (!onCooldown() && auctionCycleActive) {
            return "auctionActive";
        } else {
            return "Unknown phase";
        }
    }

    function getMotorPushesWithoutBuy() public view returns (uint256) {
        require(!onCooldown()&& auctionCycleActive);
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        // Calculate how many full small cycles have been completed since the auction started (or last buy reset the auction)
        return elapsed() / cycleDuration;
    }

    // Functions to get remaining lives

    function getRemainingLivesForAllCharacters() public view returns (uint8[] memory) {
        uint8[] memory lives = new uint8[](characters.length);
        for (uint256 i = 0; i < characters.length; i++) {
            lives[i] = 3 - assetUsageCount[characters[i]];
        }
        return lives;
    }

    function getRemainingLivesForAllObstacles() public view returns (uint8[] memory) {
        uint8[] memory lives = new uint8[](obstacles.length);
        for (uint256 i = 0; i < obstacles.length; i++) {
            lives[i] = 3 - assetUsageCount[obstacles[i]];
        }
        return lives;
    }

    function getRemainingLivesForAllSurfaces() public view returns (uint8[] memory) {
        uint8[] memory lives = new uint8[](surfaces.length);
        for (uint256 i = 0; i < surfaces.length; i++) {
            lives[i] = 3 - assetUsageCount[surfaces[i]];
        }
        return lives;
    }

    function getAllAssetsRemainingLives()
        public
        view
        returns (
            string[] memory,
            uint8[] memory,
            string[] memory,
            uint8[] memory,
            string[] memory,
            uint8[] memory
        )
    {
        string[] memory characterNames = new string[](characters.length);
        uint8[] memory characterLives = new uint8[](characters.length);
        string[] memory obstacleNames = new string[](obstacles.length);
        uint8[] memory obstacleLives = new uint8[](obstacles.length);
        string[] memory surfaceNames = new string[](surfaces.length);
        uint8[] memory surfaceLives = new uint8[](surfaces.length);

        for (uint256 i = 0; i < characters.length; i++) {
            characterNames[i] = characters[i];
            characterLives[i] = 3 - assetUsageCount[characters[i]];
        }
        for (uint256 i = 0; i < obstacles.length; i++) {
            obstacleNames[i] = obstacles[i];
            obstacleLives[i] = 3 - assetUsageCount[obstacles[i]];
        }
        for (uint256 i = 0; i < surfaces.length; i++) {
            surfaceNames[i] = surfaces[i];
            surfaceLives[i] = 3 - assetUsageCount[surfaces[i]];
        }

        return (
            characterNames,
            characterLives,
            obstacleNames,
            obstacleLives,
            surfaceNames,
            surfaceLives
        );
    }

    // Function to get the remaining time until price resets
    function remainingTimeUntilPriceReset() public view returns (uint256) {
        require (auctionCycleActive, "Auction not active");
        require (!emergencyPaused, "Auction is paused");
        require  (!onCooldown(),"Auction is on cooldown");

        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 timeSinceStart = block.timestamp - startTime;
        uint256 timeInCurrentCycle = timeSinceStart % cycleDuration;

        uint256 remainingTime;
        if (timeInCurrentCycle < decreasingDuration) {
            // If we're in the decreasing phase
            remainingTime = decreasingDuration - timeInCurrentCycle;
        } else {
            // If we're in the stable phase
            remainingTime = cycleDuration - timeInCurrentCycle;
        }
        return remainingTime;
    }


    // Function to get the remaining time till pause ends
    function remainingTimeTillPauseEnds() public view returns (uint256) {

        require  (onCooldown(),"Auction is not on cooldown");
            uint256 remainingTime = nextAuctionTime - block.timestamp;
            return remainingTime;
    }
}
