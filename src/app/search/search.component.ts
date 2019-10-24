import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { QueryBuilderService } from '../shared/services/query-builder.service';

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent implements OnInit {

  currentUrl = '';
  previousUrl = '';
  hasIdParams = false;

  constructor(
    private router: Router,
    private queryBuilder: QueryBuilderService,
    ) { }

  ngOnInit() {
    this.currentUrl = this.router.url;
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.previousUrl = this.currentUrl;
        this.currentUrl = event.url;
      }
    });
  }

  redirectTo(url) {
    this.queryBuilder.resetObject();
    this.router.navigate([`/search/${url}`]);
  }

  navigateToSearchResult() {
    this.router.navigate(['search/result']);
  }

  navigateToPreviousItem() {
    this.router.navigate([this.previousUrl]);
  }

}
