import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { QueryParam, QueryMatch } from '../../models/QueryBuilder';
import * as _ from 'lodash';
import { HomeService } from '../../services/home.service';
import { QueryBuilderService } from '../../services/query-builder.service';
import { Router } from '@angular/router';
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  options: Select2Options = {
    width: '100%'
  };

  checkBoxArray: string[] = [];
  public filterCategories: any[] = [];
  public filterQueryBuilder: QueryParam[] = [];
  public coreTypes: any[] = [];
  public dynamicTypes: any[] = [];

  constructor(
    private homeService: HomeService,
    private searchService: QueryBuilderService,
    private router: Router
    ) { }

  ngOnInit() {
    this.getUpdatedValues();

    this.homeService.getFilterValues()
      .subscribe((res: any) => {
        this.filterCategories = res.results;
      });
  }

  getUpdatedValues() {
    this.homeService.getUpdatedValues(this.filterQueryBuilder)
    .subscribe((res: any) => {
      if (res.status === 'OK') {
        this.coreTypes = res.results.core_types;
        this.dynamicTypes = res.results.dynamic_types;
      }
    });
  }

  onValueChecked(event) {

    const [i, j] = event.target.id.split(' ').map(o => parseInt(o, 10));
    const selected = this.filterCategories[i].items[j].queryParam as QueryParam;

    if (this.checkBoxArray.includes(event.target.id)) {
      this.filterQueryBuilder = this.filterQueryBuilder.filter(item => {
        return !(_.isEqual(item, selected));
      });
      this.checkBoxArray = this.checkBoxArray.filter(item => item !== event.target.id);
    } else {
      this.checkBoxArray.push(event.target.id);
      this.filterQueryBuilder.push(selected);
    }
    this.getUpdatedValues();
  }

  navigateToSearch(queryMatch: QueryMatch) {
    queryMatch.params = this.filterQueryBuilder;
    this.searchService.submitSearchResultsFromHome(queryMatch);
    this.router.navigate(['/search/result']);
  }

}
