import { Component, OnInit } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryParam, QueryMatch } from '../../shared/models/QueryBuilder';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-advanced-search',
  templateUrl: './advanced-search.component.html',
  styleUrls: ['./advanced-search.component.css'],
})
export class AdvancedSearchComponent implements OnInit {

  queryBuilderObject: QueryBuilder;
  showAdvancedFilters = false;
  operators;
  processes = [];
  public dataTypes;
  public dataModels;

  constructor(
    private queryBuilder: QueryBuilderService,
    private router: Router,
    private route: ActivatedRoute,
  ) { }

  ngOnInit() {

    this.queryBuilder.getDataTypesandModels();

    this.queryBuilderObject = this.queryBuilder.getCurrentObject();

    if (this.advancedFiltersSelected()) {
      this.showAdvancedFilters = true;
    }
  }

  advancedFiltersSelected() {
    const { processesUp, connectsUpTo, connectsDownTo } = this.queryBuilderObject;
    if (processesUp.length) {
      return true;
    }
    return (connectsUpTo || connectsDownTo);
  }

  setConnectsUpTo(event) {
    this.queryBuilderObject.connectsUpTo = event;
  }

  setConnectsDownTo(event) {
    this.queryBuilderObject.connectsDownTo = event;
  }

  onSubmit() {
    this.router.navigate(['../result'], {
      relativeTo: this.route,
      queryParams: {
        category: this.queryBuilderObject.queryMatch.category
      }
    });
    this.queryBuilder.setSearchType('advanced');
    this.queryBuilder.setQueryBuilderCache();
  }

}
