ALTER TABLE `result` MODIFY COLUMN `scan_id` int(11);
ALTER TABLE `result` DROP FOREIGN KEY `result_ibfk_1`;
ALTER TABLE `result` ADD FOREIGN KEY (`scan_id`) REFERENCES `scan` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;