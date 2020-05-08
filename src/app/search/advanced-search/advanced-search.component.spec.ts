import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MockComponent } from 'ng-mocks';
import { AdvancedSearchComponent } from './advanced-search.component';
import { createHostFactory, Spectator, SpectatorHost } from '@ngneat/spectator';
import { QueryBuilderComponent } from './query-builder/query-builder.component';
import { PropertyParamsComponent } from './query-builder/property-params/property-params.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';

describe('AdvancedSearchComponent', () => {

  let spectator: SpectatorHost<AdvancedSearchComponent>;

  const createHost = createHostFactory({
    component: AdvancedSearchComponent,
    declarations: [
      MockComponent(QueryBuilderComponent),
      MockComponent(PropertyParamsComponent)
    ],
    imports: [
      HttpClientModule,
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createHost('<app-advanced-search></app-advanced-search>'));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
