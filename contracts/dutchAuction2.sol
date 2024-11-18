// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DutchAuction {
    address public owner; // can end and emergencypause
    address public treasury; // treasury can start, end and emergencypause + receives funds
    uint256 public startTime;
    uint256 public startingPrice;
    uint256 public minPrice;
    uint256 public decreasingDuration; //time during which price goes from max to minprice
    uint256 public secondsAtBottom; // time at minprice
    uint256 public cooldown;       // set in constructor
    uint256 public initialPause;   // variable for initial pause
    uint256 public nextMintID = 1;
    bool public ended = false;
    bool public auctionCycleActive = false;
    bool public emergencyPaused = false;
    uint256 public epauseStartTime; //variable to store the timestamp of emergencyPause
    uint256 public totalBuys = 0; // counter for total buys
    uint256 public totalETHSpent = 0; // counter for total ETH spent
    uint256 public constant MAX_BUYS = 33; // Maximum number of buys before auction ends
    uint256 public constant MAX_ETH = 33 ether; // Maximum total ETH spent before auction ends

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

    modifier onlyTreasury() {
        require( msg.sender == treasury, "Only the treasury can call this function");
        _;
    }

    modifier onlyOwnerOrTreasury() {
        require(msg.sender == owner || msg.sender == treasury, "Only the owner or treasury can call this function");
        _;
    }

    modifier auctionNotOverTheCliff() {
        if (totalBuys >= MAX_BUYS || totalETHSpent + (getMotorPushesWithoutBuy() * 1.1 ether) >= MAX_ETH) {
            revert("The auction has reached its limit");
        }
        _;
    }


    modifier auctionNotEnded() {
        require(auctionCycleActive, "Auction cycle is not active");
        require(!ended, "Auction has ended");
        _;
    }

    modifier auctionCycleIsActive() {
        require(auctionCycleActive, "Auction cycle is not active");
        require(!ended, "Auction has ended");
        _;
    }

    modifier notOnCooldown() {
        require(!onCooldown(), "Auction is on cooldown");
        _;
    }

    modifier notEmergencyPaused() {
        require(!emergencyPaused, "Auction is in emergency pause");
        _;
    }

    constructor(
        uint256 _startingPrice,
        uint256 _minPrice,
        uint256 _secondsAtBottom,
        uint256 _decreasingDuration,
        uint256 _cooldown,
        uint256 _initialPause,
        address _treasury
    ) {
        require(_startingPrice > _minPrice, "Starting price should be greater than minimum price.");
        owner = msg.sender;
        treasury = _treasury;
        startingPrice = _startingPrice;
        minPrice = _minPrice;
        secondsAtBottom = _secondsAtBottom;
        decreasingDuration = _decreasingDuration;
        cooldown = _cooldown;
        initialPause = _initialPause;
        startTime = block.timestamp;

    }

    function currentPrice() public view auctionCycleIsActive notOnCooldown notEmergencyPaused returns (uint256) {
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 elapsed = (block.timestamp - startTime) % (cycleDuration + cooldown);

        uint256 timeInCycle = elapsed % cycleDuration;

        if (timeInCycle < decreasingDuration) {
            uint256 priceDrop = startingPrice - minPrice;
            return startingPrice - (priceDrop * timeInCycle / decreasingDuration);
        } else {
            return minPrice;
        }
    }

    function startAuctionCycle() external onlyTreasury notEmergencyPaused {
        require(!auctionCycleActive, "Auction cycle is already active");
        require(!ended, "Auction has ended");
        auctionCycleActive = true;
        startTime = block.timestamp + initialPause;  // Use initialPause variable

    }
    //irreversible ending of auctions
    function _endAuction() internal {
        auctionCycleActive = false;
        ended = true;

    }

    function endAuction() external onlyOwnerOrTreasury auctionCycleIsActive {
         _endAuction();
    }

    function buy(
        string memory character,
        string memory obstacle,
        string memory surface
    ) external payable auctionNotEnded notOnCooldown auctionCycleIsActive notEmergencyPaused auctionNotOverTheCliff {
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
        uint256 motorPushesCost = getMotorPushesWithoutBuy() * 1.1 ether;
        totalETHSpent += price + motorPushesCost;
        assetUsageCount[character]++;
        assetUsageCount[obstacle]++;
        assetUsageCount[surface]++;
        totalBuys++;
        startTime = block.timestamp + cooldown;
        uint256 mintID = nextMintID++;
        emit AuctionSale(msg.sender, msg.value, price, mintID, character, obstacle, surface);

        uint256 refundAmount = msg.value - price;
        if (refundAmount > 0) {
            (bool success, ) = payable(msg.sender).call{value: refundAmount}("");
            require(success, "Refund failed");
        }

        // Send the received funds to the owner address
        (bool sent, ) = payable(owner).call{value: price}("");
        require(sent, "Transfer to owner failed");
        if ( totalETHSpent >= MAX_ETH || totalBuys >= MAX_BUYS) {
            _endAuction();
        }
    }

    function emergencyPause() external onlyOwnerOrTreasury auctionCycleIsActive {
        if (emergencyPaused) {
            // Resuming from emergency pause
            emergencyPaused = false;

            // Calculate how long the contract was paused
            uint256 epauseDuration = block.timestamp - epauseStartTime;

            // Adjust the timers to resume from the point where they left off
            startTime += epauseDuration;


        } else {
            // start  emergencyPause
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

    function withdraw() external onlyOwner auctionNotEnded notEmergencyPaused {
        require(ended, "Auction must be ended to withdraw");
        payable(owner).transfer(address(this).balance);
    }

    function onCooldown() public view returns (bool) {
        if (block.timestamp < startTime) {
            return true;
        }
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 elapsed = (block.timestamp - startTime) % (cycleDuration + cooldown);

        return elapsed >= cycleDuration;
    }



    //frontend queries state
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
    //increments whenever a cooldown is initiated without a buy
    function getMotorPushesWithoutBuy() public view auctionCycleIsActive notEmergencyPaused returns (uint256) {
        if (block.timestamp < startTime) {
            return 0;
        }
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 totalDuration = cycleDuration + cooldown;
        uint256 elapsedTime = block.timestamp - startTime;
        uint256 elapsed = elapsedTime % totalDuration;
        uint256 timesTriggered = elapsedTime / totalDuration;
        if (elapsed >= cycleDuration) {
            timesTriggered += 1;
        }
        return timesTriggered;
    }

    function  motorPushedByCM () public view returns (uint256) {
        uint256 motorPushesCost = getMotorPushesWithoutBuy() * 1.1 ether;
        return totalETHSpent + motorPushesCost;

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

    function remainingTimeUntilCooldown() public view auctionCycleIsActive notOnCooldown notEmergencyPaused returns (uint256) {
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;

        uint256 elapsed = (block.timestamp - startTime) % (cycleDuration + cooldown);
        return cycleDuration - elapsed;
    }
    function remainingTimeTillPauseEnds() public view returns (uint256) {
        require(onCooldown(), "Auction is not on cooldown");
        if (startTime > block.timestamp) {
            return startTime - block.timestamp;

        }else{
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 elapsed = (block.timestamp - startTime) % (cycleDuration + cooldown);
        uint256 timeRemaining = (cycleDuration + cooldown) - elapsed;
        return timeRemaining;
        }

    }//1100000000000000000
}
