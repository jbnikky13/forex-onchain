// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TreasuryEngine is Ownable {
    struct SwapRule {
        address tokenIn;
        address tokenOut;
        uint256 triggerRate;    // Execute swap if rate >= this
        uint256 swapPercent;    // % of balance to swap (0-100)
        bool active;
    }

    address public swapContract;
    SwapRule[] public rules;

    event RuleAdded(uint256 ruleId, address tokenIn, address tokenOut);
    event RuleExecuted(uint256 ruleId, uint256 amountSwapped);

    constructor(address _swapContract) Ownable(msg.sender) {
        swapContract = _swapContract;
    }

    function addRule(
        address tokenIn,
        address tokenOut,
        uint256 triggerRate,
        uint256 swapPercent
    ) external onlyOwner returns (uint256) {
        rules.push(SwapRule(tokenIn, tokenOut, triggerRate, swapPercent, true));
        uint256 ruleId = rules.length - 1;
        emit RuleAdded(ruleId, tokenIn, tokenOut);
        return ruleId;
    }

    // Called by Chainlink Automation or keeper bots
    function executeRule(uint256 ruleId, uint256 currentRate) external {
        SwapRule storage rule = rules[ruleId];
        require(rule.active, "Rule inactive");
        require(currentRate >= rule.triggerRate, "Rate condition not met");

        uint256 balance = IERC20(rule.tokenIn).balanceOf(address(this));
        uint256 swapAmount = (balance * rule.swapPercent) / 100;

        IERC20(rule.tokenIn).approve(swapContract, swapAmount);
        // Call StableFXSwap
        (bool success, ) = swapContract.call(
            abi.encodeWithSignature(
                "swap(address,address,uint256,uint256)",
                rule.tokenIn, rule.tokenOut, swapAmount, 0
            )
        );
        require(success, "Swap failed");
        emit RuleExecuted(ruleId, swapAmount);
    }
}
