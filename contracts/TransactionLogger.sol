// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract TransactionLogger {
    address public immutable owner;

    event TransactionRecorded(
        address indexed user,
        uint256 amount,
        string note,
        uint256 timestamp
    );

    constructor() {
        owner = msg.sender;
    }

    function makeTransaction(string calldata note) external payable {
        require(msg.value > 0, "Amount must be greater than zero");
        emit TransactionRecorded(msg.sender, msg.value, note, block.timestamp);
    }

    function withdraw() external {
        require(msg.sender == owner, "Only owner");
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance to withdraw");
        payable(owner).transfer(balance);
    }
}
