plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "2.1.20"
    id("org.jetbrains.intellij.platform") version "2.17.0"
}

group = "com.chelayel.tidepets"
// A tag builds and publishes at the tag's version (release.yml); gradle.properties
// only labels local builds and builds off main.
version = (findProperty("pluginVersion") as String?) ?: "0.0.0"

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        // IntelliJ IDEA Community; works in every JetBrains IDE built on the platform.
        create("IC", "2024.2.5")
    }
}

intellijPlatform {
    instrumentCode = false
    buildSearchableOptions = false
    pluginConfiguration {
        version = project.version.toString()
        ideaVersion {
            sinceBuild = "242"
            untilBuild = provider { null }
        }
    }
    // `./gradlew publishPlugin` with JETBRAINS_MARKETPLACE_TOKEN set (a token from
    // https://plugins.jetbrains.com/author/me/tokens). The first upload of a new
    // plugin is done by hand on the Marketplace site; this handles updates.
    publishing {
        token = providers.environmentVariable("JETBRAINS_MARKETPLACE_TOKEN")
    }
    pluginVerification {
        ides {
            // JetBrains' pick of IDE builds for the declared since-build range.
            recommended()
        }
    }
}

// One pet page for both IDEs: it lives in web/ and is copied in at build.
tasks.processResources {
    from(rootDir.resolve("../web")) { into("pet") }
}

kotlin {
    jvmToolchain(21)
}
