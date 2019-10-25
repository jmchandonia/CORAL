import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryParam, QueryMatch } from '../../shared/models/QueryBuilder';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

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
    private http: HttpClient,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {

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

  removeProcessUp(index) {
    const { processesUp } = this.queryBuilderObject;
    this.queryBuilderObject.processesUp = processesUp.filter((_, i) => i !== index);
  }

  addProcessUp() {
    this.queryBuilderObject.processesUp.push(new QueryParam());
  }

  setConnectsUpTo(event) {
    this.queryBuilderObject.connectsUpTo = event;
  }

  setConnectsDownTo(event) {
    this.queryBuilderObject.connectsDownTo = event;
  }

  onSubmit() {
    this.router.navigate(['../result'], {relativeTo: this.route});
    this.queryBuilder.setSearchType('advanced');
  }

  clear() {
    this.queryBuilder.resetObject();
  }

}
