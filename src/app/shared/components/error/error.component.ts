import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-error',
  templateUrl: './error.component.html',
  styleUrls: ['./error.component.css']
})
export class ErrorComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) { }

  data: any;
  message: string;
  status: string;

  ngOnInit() {
    this.route.paramMap.subscribe((p: any) => {
      this.status = p.params.status;
      this.message = p.params.message;
    });

  }

}
