// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract LimitedMintRoyaltyNFT is ERC721URIStorage, ERC2981, Ownable {
    uint256 public totalMinted;
    uint256 public constant MAX_SUPPLY = 33;

    constructor(string memory name, string memory symbol, address royaltyReceiver, uint96 royaltyFeeNumerator) ERC721(name, symbol) {
        // Setting default royalty for all NFTs minted through this contract
        _setDefaultRoyalty(royaltyReceiver, royaltyFeeNumerator);
    }

    function mintNFT(address to, string memory tokenURI) external onlyOwner {
        require(totalMinted < MAX_SUPPLY, "Maximum NFT supply reached");
        require(to != address(0), "Cannot mint to zero address");
        require(bytes(tokenURI).length > 0, "Token URI cannot be empty");
        uint256 tokenId = totalMinted + 1;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        totalMinted++;
    }

    // The following functions are overrides required by Solidity.
    // This contract supports ERC721, ERC2981 interfaces.
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, ERC2981) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
