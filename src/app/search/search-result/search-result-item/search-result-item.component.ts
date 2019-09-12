import { Component, OnInit } from '@angular/core';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-search-result-item',
  templateUrl: './search-result-item.component.html',
  styleUrls: ['./search-result-item.component.css']
})
export class SearchResultItemComponent implements OnInit {

  public searchResult: any;
  private objectId: string;

  constructor(
    private qb: QueryBuilderService,
    private route: ActivatedRoute,
    private router: Router
    ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params.id) {
        this.objectId = params.id;
        this.qb.getObjectMetadata(this.objectId)
          .subscribe(result => {
            this.searchResult = result;
          });
      }
    });
  }

  useForPlot() {
    this.router.navigate([`/plot/options/${this.objectId}`]);
  }

}
