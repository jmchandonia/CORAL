import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { QueryBuilderService } from '../shared/services/query-builder.service';

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent implements OnInit, OnDestroy {

  currentUrl = '';
  previousUrl = '';
  hasIdParams = false;
  navigatedFromHome = false;

  constructor(
    private router: Router,
    private queryBuilder: QueryBuilderService,
    private route: ActivatedRoute
    ) { }

  ngOnInit() {
    this.currentUrl = this.router.url;
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.previousUrl = this.currentUrl;
        this.currentUrl = event.url;
      }
    });
    this.route.queryParams.subscribe(params => {
      if (params['redirect']) {
        this.navigatedFromHome = true;
      }
    });
  }

  ngOnDestroy() {
    if (!this.navigatedFromHome) {
      this.queryBuilder.resetObject();
    }
  }

  redirectTo(url) {
    this.queryBuilder.resetObject();
    this.router.navigate([`/search/${url}`]);
  }

  navigateToSearchResult() {
    const queryParams = this.navigatedFromHome ? { redirect: 'home' } : {}
    this.router.navigate(['search/result'], {queryParams});
  }

  navigateToPreviousItem() {
    this.router.navigate([this.previousUrl]);
  }
}
