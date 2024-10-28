/*M!999999\- enable the sandbox mode */
-- MariaDB dump 10.19  Distrib 10.5.26-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: downonly
-- ------------------------------------------------------
-- Server version	10.5.26-MariaDB-0+deb11u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `mints3`
--

DROP TABLE IF EXISTS `mints6`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mints6` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `jobState` varchar(255) DEFAULT NULL,
  `surface` varchar(255) DEFAULT NULL,
  `surfaceSmiley` varchar(255) DEFAULT NULL,
  `obstacle` varchar(255) DEFAULT NULL,
  `obstacleSmiley` varchar(255) DEFAULT NULL,
  `figure` varchar(255) DEFAULT NULL,
  `figureSmiley` varchar(255) DEFAULT NULL,
  `openSea` varchar(255) DEFAULT NULL,
  `ipfsMP3` varchar(255) DEFAULT NULL,
  `ipfsJPG` varchar(255) DEFAULT NULL,
  `ipfsMP4` varchar(255) DEFAULT NULL,
  `ipfsGLB` varchar(255) DEFAULT NULL,
  `mintprice` varchar(100) DEFAULT NULL,
  `fullname` varchar(100) DEFAULT NULL,
  `mintdate` datetime DEFAULT current_timestamp(),
  `buyerAddress` varchar(255) DEFAULT NULL,
  `buytxHash` varchar(255) DEFAULT NULL,
  `blockHeight` int(20) DEFAULT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
GRANT SELECT ON downonly.mints6 TO 'frontend'@'%';

-- Dump completed on 2024-09-17 18:39:48
