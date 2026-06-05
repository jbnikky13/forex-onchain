// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract StableFXSwap is Ownable {
    // Registered stablecoin pairs e.g. USDC, EURC, MXNB
    mapping(address => mapping(address => uint256)) public exchangeRates;
    mapping(address => bool) public supportedTokens;

    event SwapExecuted(
        address indexed user,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );

    event RateUpdated(address tokenIn, address tokenOut, uint256 rate);

    constructor() Ownable(msg.sender) {}

    function addSupportedToken(address token) external onlyOwner {
        supportedTokens[token] = true;
    }

    function setExchangeRate(
        address tokenIn,
        address tokenOut,
        uint256 rate  // rate with 18 decimal precision
    ) external onlyOwner {
        exchangeRates[tokenIn][tokenOut] = rate;
        emit RateUpdated(tokenIn, tokenOut, rate);
    }

    function swap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256 amountOut) {
        require(supportedTokens[tokenIn], "Token not supported");
        require(supportedTokens[tokenOut], "Token not supported");
        require(exchangeRates[tokenIn][tokenOut] > 0, "No rate set");

        amountOut = (amountIn * exchangeRates[tokenIn][tokenOut]) / 1e18;
        require(amountOut >= minAmountOut, "Slippage too high");

        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenOut).transfer(msg.sender, amountOut);

        emit SwapExecuted(msg.sender, tokenIn, tokenOut, amountIn, amountOut);
        return amountOut;
    }
}
