import { Component, OnInit } from '@angular/core';
import { QueryParam, QueryMatch, QueryBuilder, Process } from '../../models/QueryBuilder';
import { isEqual } from 'lodash';
import { HomeService } from '../../services/home.service';
import { QueryBuilderService } from '../../services/query-builder.service';
import { Router } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  checkBoxArray: string[] = [];
  public filterCategories: any[] = [];
  public coreTypes: any;
  public dynamicTypes: any;
  public loading = false;

  query: QueryBuilder;

  constructor(
    private homeService: HomeService,
    private searchService: QueryBuilderService,
    private router: Router,
    private spinner: NgxSpinnerService
    ) { }

  ngOnInit() {
    this.query = this.searchService.getCurrentObject();
    this.homeService.getProvenanceGraphData();

    this.homeService.getFilterValues()
      .subscribe((res: any) => {
        this.filterCategories = res.results;
      });
  }

  getUpdatedValues() {
    this.homeService.getProvenanceGraphData(this.query.processesUp);
  }

  onValueChecked(event) {
    const [i, j] = event.target.id.split('_').map(o => parseInt(o, 10));
    const selected = this.filterCategories[i].items[j].queryParam as QueryParam;

    if (this.checkBoxArray.includes(event.target.id)) {
      this.query.processesUp = this.query.processesUp.filter(item => {
        return !(isEqual(item, selected));
      });
      this.checkBoxArray = this.checkBoxArray.filter(item => item !== event.target.id);
    } else {
      this.checkBoxArray.push(event.target.id);
      this.query.processesUp.push(selected);
    }
  }

  navigateToSearch({query, processes}: {query: QueryMatch, processes: Process[]}) {
    this.query.queryMatch = query;
    this.query.parentProcesses = processes;
    this.router.navigate(['/search/result'], {queryParams: {redirect: 'home'}});
  }

}
