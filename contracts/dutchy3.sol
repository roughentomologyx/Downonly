// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DutchAuction {
    address public owner;
    uint256 public startTime;
    uint256 public startingPrice;
    uint256 public minPrice;
    uint256 public decreasingDuration;
    uint256 public secondsAtBottom;
    uint256 public cooldown = 1 minutes;  // 1 hour in the comment but 1 minute in value
    uint256 public nextAuctionTime;
    bool public ended = false;
    bool public auctionCycleActive = false;

    string[] public characters = ["rk2", "grf"];
    string[] public obstacles = ["wc1", "elwa"];
    string[] public surfaces = ["547", "702"];

    event Payment(
        address _from,
        uint amount,
        uint price,
        string character,
        string obstacle,
        string surface
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can call this function");
        _;
    }

    modifier auctionNotEnded() {
        require(auctionCycleActive && (!ended || block.timestamp >= nextAuctionTime), "Auction has ended or not yet started");
        _;
    }

    constructor(
        uint256 _startingPrice,
        uint256 _minPrice,
        uint256 _secondsAtBottom,
        uint256 _decreasingDuration
    ) {
        require(_startingPrice > _minPrice, "Starting price should be greater than minimum price.");
        owner = msg.sender;
        startingPrice = _startingPrice;
        minPrice = _minPrice;
        secondsAtBottom = _secondsAtBottom;
        decreasingDuration = _decreasingDuration;
        startTime = block.timestamp;
        nextAuctionTime = 0;
    }

    function currentPrice() public view returns (uint256) {
        uint256 elapsed = block.timestamp - startTime;
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        uint256 timeInCycle = elapsed % cycleDuration;

        if (timeInCycle < decreasingDuration) {
            uint256 priceDrop = startingPrice - minPrice;
            return startingPrice - (priceDrop * timeInCycle /  cycleDuration);
        } else {
            return minPrice;
        }
    }

    function startAuctionCycle() external onlyOwner {
        require(!auctionCycleActive, "Auction cycle is already active");
        auctionCycleActive = true;
        startTime = block.timestamp;
        nextAuctionTime = startTime;
    }

    function endAuctionCycle() external onlyOwner {
        require(auctionCycleActive, "Auction cycle is not active");
        auctionCycleActive = false;
        ended = true;
        nextAuctionTime = 0;
    }

    function buy(string memory character, string memory obstacle, string memory surface) external payable auctionNotEnded {
        require(containedIn(character, characters), "Invalid character choice");
        require(containedIn(obstacle, obstacles), "Invalid obstacle choice");
        require(containedIn(surface, surfaces), "Invalid surface choice");
        uint256 price = currentPrice();
        require(msg.value >= price, "Bid amount is lower than the current price");
        uint256 refundAmount = msg.value - price;
        if (refundAmount > 0) {
            payable(msg.sender).transfer(refundAmount);
        }
        nextAuctionTime = block.timestamp + cooldown;
        startTime = nextAuctionTime;
        emit Payment(msg.sender, msg.value, price, character, obstacle, surface);
    }

    function containedIn(string memory value, string[] memory array) internal pure returns (bool) {
        for (uint256 i = 0; i < array.length; i++) {
            if (keccak256(abi.encodePacked(value)) == keccak256(abi.encodePacked(array[i]))) {
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

    function elapsed() public view returns (uint256) {
        return block.timestamp - startTime;
    }

   function timeInCycle() public view returns (uint256) {
        uint256 cycleDuration = decreasingDuration + secondsAtBottom;
        return elapsed() % cycleDuration;
    }

    function timeAfterDeath() public view returns (uint256) {
        uint256 tic = timeInCycle();
        return tic > secondsAtBottom ? tic - secondsAtBottom : 0;
    }

}
