// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DutchAuction {
    address public owner;
    uint256 public startPrice;
    uint256 public decreaseRate; // Amount to decrease per second
    uint256 public startTime;
    uint256 public cooldown = 1 hours;
    uint256 public nextAuctionTime;
    bool public ended = false;

    string[] public characters = ["rk2", "grf"];
    string[] public obstacles = ["wc1", "elwa"];
    string[] public surfaces = ["547", "702"];

    event AuctionEnded(address winner, uint256 winningBid, string character, string obstacle, string surface);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can call this function");
        _;
    }

    modifier auctionNotEnded() {
        require(!ended || block.timestamp >= nextAuctionTime, "Auction has already ended or not yet started");
        _;
    }

    constructor(uint256 _startPrice, uint256 _decreaseRate) {
        owner = msg.sender;
        startPrice = _startPrice;
        decreaseRate = _decreaseRate;
        startTime = block.timestamp;
        nextAuctionTime = startTime + cooldown;
    }

    function currentPrice() public view returns (uint256) {
        uint256 elapsed = block.timestamp - startTime;
        if (startPrice <= elapsed * decreaseRate) {
            return 0; // Price cannot go negative
        }
        return startPrice - elapsed * decreaseRate;
    }

    function buy(string memory character, string memory obstacle, string memory surface) external payable auctionNotEnded {
        require(block.timestamp >= nextAuctionTime, "Auction not yet started");
        require(containedIn(character, characters), "Invalid character choice");
        require(containedIn(obstacle, obstacles), "Invalid obstacle choice");
        require(containedIn(surface, surfaces), "Invalid surface choice");
        require(msg.value >= currentPrice(), "Bid amount is lower than the current price");

        if (ended) {
            // Start the auction again
            startTime = block.timestamp;
            ended = false;
        } else {
            ended = true;
            nextAuctionTime = block.timestamp + cooldown;
            emit AuctionEnded(msg.sender, msg.value, character, obstacle, surface);
        }
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
}