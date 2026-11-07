CREATE TABLE `categorias` (
  `id_categoria` int NOT NULL,
  `nombre` varchar(40) NOT NULL,
  PRIMARY KEY (`id_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CategorÃ­as de producto';

CREATE TABLE `detalle_venta` (
  `id_venta` int NOT NULL,
  `id_producto` int NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(8,2) NOT NULL COMMENT 'Precio cobrado por unidad en esa venta',
  PRIMARY KEY (`id_venta`,`id_producto`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `detalle_venta_ibfk_1` FOREIGN KEY (`id_venta`) REFERENCES `ventas` (`id_venta`),
  CONSTRAINT `detalle_venta_ibfk_2` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Productos incluidos en cada venta';

CREATE TABLE `empleados` (
  `id_empleado` int NOT NULL,
  `nombre` varchar(40) NOT NULL,
  `apellido` varchar(40) NOT NULL,
  `id_sucursal` int NOT NULL,
  `puesto` varchar(30) DEFAULT NULL COMMENT 'cajero, farmaceutico o gerente',
  `salario` decimal(10,2) DEFAULT NULL COMMENT 'Salario mensual en quetzales',
  `fecha_ingreso` date DEFAULT NULL,
  `id_jefe` int DEFAULT NULL COMMENT 'Empleado al que reporta; NULL si no tiene jefe',
  PRIMARY KEY (`id_empleado`),
  KEY `id_sucursal` (`id_sucursal`),
  KEY `id_jefe` (`id_jefe`),
  CONSTRAINT `empleados_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursales` (`id_sucursal`),
  CONSTRAINT `empleados_ibfk_2` FOREIGN KEY (`id_jefe`) REFERENCES `empleados` (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `productos` (
  `id_producto` int NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `id_categoria` int NOT NULL,
  `id_proveedor` int NOT NULL,
  `precio` decimal(8,2) NOT NULL COMMENT 'Precio de venta al pÃºblico en quetzales',
  `requiere_receta` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1 si necesita receta mÃ©dica',
  PRIMARY KEY (`id_producto`),
  KEY `id_categoria` (`id_categoria`),
  KEY `id_proveedor` (`id_proveedor`),
  CONSTRAINT `productos_ibfk_1` FOREIGN KEY (`id_categoria`) REFERENCES `categorias` (`id_categoria`),
  CONSTRAINT `productos_ibfk_2` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores` (`id_proveedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `proveedores` (
  `id_proveedor` int NOT NULL,
  `nombre` varchar(60) NOT NULL,
  `pais` varchar(40) DEFAULT NULL COMMENT 'PaÃ­s de origen del proveedor',
  PRIMARY KEY (`id_proveedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `sucursales` (
  `id_sucursal` int NOT NULL,
  `nombre` varchar(60) NOT NULL,
  `ciudad` varchar(40) NOT NULL,
  `fecha_apertura` date DEFAULT NULL COMMENT 'Fecha en que abriÃ³ la sucursal',
  PRIMARY KEY (`id_sucursal`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Sucursales de la cadena de farmacias';

CREATE TABLE `ventas` (
  `id_venta` int NOT NULL,
  `id_sucursal` int NOT NULL,
  `id_empleado` int NOT NULL COMMENT 'Empleado que registrÃ³ la venta',
  `fecha` datetime NOT NULL,
  `metodo_pago` varchar(15) DEFAULT NULL COMMENT 'efectivo, tarjeta o transferencia',
  PRIMARY KEY (`id_venta`),
  KEY `id_sucursal` (`id_sucursal`),
  KEY `id_empleado` (`id_empleado`),
  CONSTRAINT `ventas_ibfk_1` FOREIGN KEY (`id_sucursal`) REFERENCES `sucursales` (`id_sucursal`),
  CONSTRAINT `ventas_ibfk_2` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Encabezado de cada venta';
