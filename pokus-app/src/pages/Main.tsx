import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"


export default function Main() {
  console.log('Main page')
  return (
      <main className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 md:grid-rows-1 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$45,231.89</div>
              <p className="text-xs text-green-500 flex items-center mt-1">
                <span>+20.1%</span>
                <span className="ml-1">from last month</span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Subscriptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+2,350</div>
              <p className="text-xs text-green-500 flex items-center mt-1">
                <span>+10.5%</span>
                <span className="ml-1">from last month</span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+12,234</div>
              <p className="text-xs text-red-500 flex items-center mt-1">
                <span>-3.2%</span>
                <span className="ml-1">from last month</span>
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+12,234</div>
              <p className="text-xs text-red-500 flex items-center mt-1">
                <span>-3.2%</span>
                <span className="ml-1">from last month</span>
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your team's latest actions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start space-x-4">
                    <Avatar>
                      <AvatarImage src="/api/placeholder/32/32" alt="Avatar" />
                      <AvatarFallback>JD</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">Jane Doe</p>
                        <span className="text-xs">2h ago</span>
                      </div>
                      <p className="text-sm">
                        Updated the project brief for "Mobile App Redesign"
                      </p>
                    </div>
                  </div>

                  {/* Activity Item 2 */}
                  <div className="flex items-start space-x-4">
                    <Avatar>
                      <AvatarImage src="/api/placeholder/32/32" alt="Avatar" />
                      <AvatarFallback>MJ</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">Mike Johnson</p>
                        <span className="text-xs">5h ago</span>
                      </div>
                      <p className="text-sm">
                        Commented on "Landing Page Design" and uploaded 3 new files
                      </p>
                    </div>
                  </div>

                  {/* Activity Item 3 */}
                  <div className="flex items-start space-x-4">
                    <Avatar>
                      <AvatarImage src="/api/placeholder/32/32" alt="Avatar" />
                      <AvatarFallback>SL</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">Sarah Lin</p>
                        <span className="text-xs">1d ago</span>
                      </div>
                      <p className="text-sm">
                        Completed task "Finalize Q1 Budget Report"
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="w-full">View All Activity</Button>
              </CardFooter>
            </Card>

            {/* Projects Card */}
            <Card>
              <CardHeader>
                <CardTitle>ГОЛОВА</CardTitle>
                <CardDescription>подголовье</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">Annual Report</h3>
                        <p className="text-sm">Finance Team</p>
                      </div>
                      <Badge className="bg-green-500">Completed</Badge>
                    </div>
                    <div className="w-full h-2 rounded-full mt-2">
                      <div className="bg-green-500 h-2 rounded-full w-full"></div>
                    </div>
                    <div className="flex justify-between text-xs mt-2">
                      <span>Completed</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="w-full">Фуфел</Button>
              </CardFooter>
            </Card>
          </div>

          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Team Members</CardTitle>
                <CardDescription>Your project collaborators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Team Member 1 */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Avatar>
                        <AvatarImage src="/api/placeholder/36/36" alt="Avatar" />
                        <AvatarFallback>JD</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">Jane Doe</p>
                        <p className="text-sm">Product Designer</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">Message</Button>
                  </div>

                  {/* Team Member 2 */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Avatar>
                        <AvatarImage src="/api/placeholder/36/36" alt="Avatar" />
                        <AvatarFallback>MJ</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">Mike Johnson</p>
                        <p className="text-sm">Frontend Developer</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">Message</Button>
                  </div>

                  {/* Team Member 3 */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Avatar>
                        <AvatarImage src="/api/placeholder/36/36" alt="Avatar" />
                        <AvatarFallback>SL</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">Sarah Lin</p>
                        <p className="text-sm">Project Manager</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">Message</Button>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="w-full">View All Team Members</Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Frequently used tools</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full justify-start">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  Create New Project
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  Schedule Meeting
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  Send Message
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                  </svg>
                  Bookmark Report
                </Button>
              </CardContent>
            </Card>

            {/* Newsletter Signup Card */}
            <Card>
              <CardHeader>
                <CardTitle>Newsletter</CardTitle>
                <CardDescription>Get weekly updates</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input type="email" placeholder="Enter your email" />
                <Button className="w-full">Subscribe</Button>
              </CardContent>
              <CardFooter className="text-xs">
                We'll never share your email with anyone else.
              </CardFooter>
            </Card>
          </div>
        </div>
      </main>
  )
}