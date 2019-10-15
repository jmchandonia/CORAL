import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, Params } from '@angular/router';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';

@Component({
  selector: 'app-search-result-core-item',
  templateUrl: './search-result-core-item.component.html',
  styleUrls: ['./search-result-core-item.component.css']
})
export class SearchResultCoreItemComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private queryBuilder: QueryBuilderService
  ) { }

  objectId: string;
  data: any[];

  ngOnInit() {
    this.route.params.subscribe((params: Params) => {
      this.objectId = params.id;
      this.queryBuilder.getCoreTypeMetadata(this.objectId)
        .subscribe((data: any) => {
          // this.data = result;
          this.data = data.results;
        });
    });
  }

}
