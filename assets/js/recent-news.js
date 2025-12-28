const { createApp } = Vue;

createApp({
  data() {
    return {
      news: [],
      loading: true,
      error: null
    }
  },
  async mounted() {
    await this.loadNews();
  },
  methods: {
    async loadNews() {
      try {
        this.loading = true;
        const response = await fetch('assets/data/news.json');
        const data = await response.json();
        
        // Take only the first 5 items
        this.news = data.news.slice(0, 5);
        this.loading = false;
      } catch (error) {
        this.error = error.message;
        this.loading = false;
        console.error('Error loading news data:', error);
      }
    }
  },
  template: `
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else-if="error" class="alert alert-danger" role="alert">
      Error loading data: {{ error }}
    </div>
    
    <div v-else>
      <ul class="simple-news-list">
        <li v-for="item in news" :key="item.id">
          <strong>{{ item.date }}:</strong> {{ item.content }}
          <a v-if="item.link" :href="item.link.url" target="_blank" class="ms-1">
            [{{ item.link.text }}]
          </a>
        </li>
      </ul>
    </div>
  `
}).mount('#recent-news-app');
