const hre = require("hardhat");
const fs = require("fs");
require("dotenv").config();

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = hre.network.name;

  console.log(`\n🚀 Deploying to ${network}`);
  console.log(`📬 Deployer: ${deployer.address}`);
  console.log(`💰 Balance: ${hre.ethers.formatEther(
    await hre.ethers.provider.getBalance(deployer.address)
  )} ETH\n`);

  // 1. Deploy MultiSig
  console.log("1️⃣  Deploying MultiSigGuard...");
  const MultiSig = await hre.ethers.getContractFactory("MultiSigGuard");
  const multiSig = await MultiSig.deploy(
    deployer.address,
    deployer.address,
    deployer.address
  );
  await multiSig.waitForDeployment();
  const multiSigAddr = await multiSig.getAddress();
  console.log(`   ✅ MultiSig: ${multiSigAddr}`);

  // 2. Deploy Swap
  console.log("2️⃣  Deploying StableFXSwap...");
  const Swap = await hre.ethers.getContractFactory("StableFXSwap");
  const swap = await Swap.deploy(deployer.address, multiSigAddr);
  await swap.waitForDeployment();
  const swapAddr = await swap.getAddress();
  console.log(`   ✅ StableFXSwap: ${swapAddr}`);

  // 3. Deploy Treasury
  console.log("3️⃣  Deploying TreasuryEngine...");
  const Treasury = await hre.ethers.getContractFactory("TreasuryEngine");
  const treasury = await Treasury.deploy(swapAddr);
  await treasury.waitForDeployment();
  const treasuryAddr = await treasury.getAddress();
  console.log(`   ✅ TreasuryEngine: ${treasuryAddr}`);

  // 4. Save addresses
  const addresses = {
    network,
    multiSig: multiSigAddr,
    swap: swapAddr,
    treasury: treasuryAddr,
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync("deployments.json", JSON.stringify(addresses, null, 2));
  console.log("\n✅ Deployments saved to deployments.json");
  console.log(JSON.stringify(addresses, null, 2));
}

main().catch((error) => {
  console.error("❌ Deploy failed:", error);
  process.exit(1);
});
