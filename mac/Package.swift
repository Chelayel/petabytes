// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Petabytes",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "Petabytes", path: "Sources/Petabytes"),
        .testTarget(name: "PetabytesTests", dependencies: ["Petabytes"], path: "Tests")
    ]
)
