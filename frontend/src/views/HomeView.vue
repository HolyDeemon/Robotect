<script setup>
import AppHeader from '../components/AppHeader.vue'
import HeroSection from '../components/HeroSection.vue'
import HowItWorks from '../components/HowItWorks.vue'
import FeatureGrid from '../components/FeatureGrid.vue'
import SiteFooter from '../components/SiteFooter.vue'
</script>

<template>
  <div class="page">
    <AppHeader />
    <HeroSection />
    <FeatureGrid />
    <HowItWorks />
    <SiteFooter />
  </div>
</template>

<style scoped>
.page {
  width: min(1200px, calc(100% - 40px));
  margin: 20px auto 0;
}
</style>
